#!/usr/bin/env python3
"""
Production-ready longitudinal cancer evolution analysis pipeline.

This script implements iterative Bayesian tree updating using blood sample data
for temporal cancer monitoring. It processes tree distributions from the aggregation
stage and updates them based on ddPCR measurements from liquid biopsy samples.

Usage:
    python longitudinal_update.py PATIENT_ID \
        --aggregation-dir /path/to/aggregation_results \
        --ssm-file /path/to/ssm.txt \
        --longitudinal-data /path/to/longitudinal_data.csv \
        --output-dir /path/to/output \
        --n-markers 2

Authors: TracerX Pipeline Development Team
Version: 1.0.0
"""

import argparse
import logging
import os
import sys
import pickle
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Import local modules from the 5-long directory
from optimize import *
from optimize_fraction import *
from analyze import *
from adjust_tree_distribution import *


def setup_logging(output_dir: Path, patient_id: str) -> logging.Logger:
    """
    Set up comprehensive logging for the longitudinal analysis pipeline.
    
    Args:
        output_dir: Directory where log files will be stored
        patient_id: Patient identifier for log file naming
        
    Returns:
        Configured logger instance
    """
    # Create logs directory
    log_dir = output_dir / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create timestamp for log file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f'{patient_id}_longitudinal_analysis_{timestamp}.log'
    
    # Configure logging format
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger('longitudinal_analysis')
    logger.info(f"Starting longitudinal analysis for patient {patient_id}")
    logger.info(f"Log file: {log_file}")
    
    return logger


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments for the longitudinal analysis pipeline.
    
    Returns:
        Parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description='Run longitudinal cancer evolution analysis with iterative Bayesian tree updating',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Basic longitudinal analysis
    python longitudinal_update.py CRUK0044 \\
        --aggregation-dir /data/CRUK0044/initial/aggregation_results \\
        --ssm-file /data/ssm.txt \\
        --longitudinal-data /data/CRUK0044_longitudinal.csv \\
        --output-dir /data/CRUK0044/longitudinal

    # Advanced configuration
    python longitudinal_update.py CRUK0041 \\
        --aggregation-dir /data/CRUK0041/aggregation_results \\
        --ssm-file /data/ssm.txt \\
        --longitudinal-data /data/CRUK0041_ddpcr.csv \\
        --output-dir /data/CRUK0041/longitudinal \\
        --n-markers 3 \\
        --read-depth 95000 \\
        --algorithm struct \\
        --timepoints 2024-01-15,2024-02-15,2024-03-15
        """
    )
    
    # Required arguments
    parser.add_argument('patient_id', type=str,
                       help='Patient identifier (e.g., CRUK0044)')
    
    parser.add_argument('-a', '--aggregation-dir', type=str, required=True,
                       help='Path to aggregation results directory containing tree distributions')
    
    parser.add_argument('-s', '--ssm-file', type=str, required=True,
                       help='Path to SSM file containing tissue mutation data')
    
    parser.add_argument('-l', '--longitudinal-data', type=str, required=True,
                       help='Path to CSV file containing longitudinal ddPCR data')
    
    parser.add_argument('-o', '--output-dir', type=str, required=True,
                       help='Output directory for longitudinal analysis results')
    
    # Analysis parameters
    parser.add_argument('-n', '--n-markers', type=int, default=2,
                       help='Number of markers to select for each timepoint (default: 2)')
    
    parser.add_argument('-r', '--read-depth', type=int, default=90000,
                       help='Expected read depth for ddPCR analysis (default: 90000)')
    
    parser.add_argument('--algorithm', type=str, choices=['struct', 'frac'], default='struct',
                       help='Algorithm type for marker selection (default: struct)')
    
    parser.add_argument('--method', type=str, default='phylowgs',
                       help='Phylogenetic method used (default: phylowgs)')
    
    # Optional filtering and configuration
    parser.add_argument('-t', '--timepoints', type=str,
                       help='Comma-separated list of timepoints to analyze (YYYY-MM-DD format). If not specified, all timepoints in data will be used.')
    
    parser.add_argument('--lambda1', type=float, default=0,
                       help='Weight for tree fractions in optimization (default: 0)')
    
    parser.add_argument('--lambda2', type=float, default=1,
                       help='Weight for tree distributions in optimization (default: 1)')
    
    parser.add_argument('--focus-sample', type=int, default=0,
                       help='Sample index to focus on for marker selection (default: 0)')
    
    # Output and visualization options
    parser.add_argument('--no-plots', action='store_true',
                       help='Skip generation of visualization plots')
    
    parser.add_argument('--plot-format', type=str, choices=['png', 'pdf', 'eps'], default='png',
                       help='Output format for plots (default: png)')
    
    parser.add_argument('--save-intermediate', action='store_true',
                       help='Save intermediate results for debugging')
    
    # Validation and debugging
    parser.add_argument('--validate-inputs', action='store_true', default=True,
                       help='Validate input data compatibility (default: True)')
    
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging and save additional intermediate files')
    
    return parser.parse_args()


def validate_input_files(args: argparse.Namespace, logger: logging.Logger) -> bool:
    """
    Validate that all required input files exist and are accessible.
    
    Args:
        args: Parsed command line arguments
        logger: Logger instance for reporting
        
    Returns:
        True if all validations pass, False otherwise
    """
    logger.info("Validating input files...")
    
    # Check aggregation directory and required files
    aggregation_dir = Path(args.aggregation_dir)
    if not aggregation_dir.exists():
        logger.error(f"Aggregation directory not found: {aggregation_dir}")
        return False
    
    # Check for required aggregation files
    required_files = [
        'phylowgs_bootstrap_summary.pkl',
        'phylowgs_bootstrap_aggregation.pkl'
    ]
    
    for req_file in required_files:
        file_path = aggregation_dir / req_file
        if not file_path.exists():
            logger.error(f"Required aggregation file not found: {file_path}")
            return False
        logger.info(f"Found required file: {file_path}")
    
    # Check SSM file
    ssm_file = Path(args.ssm_file)
    if not ssm_file.exists():
        logger.error(f"SSM file not found: {ssm_file}")
        return False
    logger.info(f"Found SSM file: {ssm_file}")
    
    # Check longitudinal data file
    longitudinal_file = Path(args.longitudinal_data)
    if not longitudinal_file.exists():
        logger.error(f"Longitudinal data file not found: {longitudinal_file}")
        return False
    logger.info(f"Found longitudinal data file: {longitudinal_file}")
    
    # Create output directory if it doesn't exist
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {output_dir}")
    
    logger.info("All input file validations passed")
    return True


def load_tree_distributions(aggregation_dir: Path, method: str, logger: logging.Logger) -> Tuple[Dict, Dict]:
    """
    Load tree distribution data from aggregation stage outputs.
    
    Args:
        aggregation_dir: Path to aggregation results directory
        method: Phylogenetic method used (e.g., 'phylowgs')
        logger: Logger instance for reporting
        
    Returns:
        Tuple of (tree_distribution_summary, tree_distribution_full)
    """
    logger.info("Loading tree distribution data from aggregation stage...")
    
    # Load summary tree distribution
    summary_file = aggregation_dir / f'{method}_bootstrap_summary.pkl'
    with open(summary_file, 'rb') as f:
        tree_distribution_summary = pickle.load(f)
    logger.info(f"Loaded tree distribution summary: {len(tree_distribution_summary['tree_structure'])} trees")
    
    # Load full tree distribution data
    full_file = aggregation_dir / f'{method}_bootstrap_aggregation.pkl'
    with open(full_file, 'rb') as f:
        tree_distribution_full = pickle.load(f)
    logger.info(f"Loaded full tree distribution data: {len(tree_distribution_full['tree_structure'])} trees")
    
    return tree_distribution_summary, tree_distribution_full


def load_tissue_data_from_ssm(ssm_file: Path, logger: logging.Logger) -> Tuple[pd.DataFrame, Dict, List]:
    """
    Load and process tissue mutation data from SSM file format.
    
    This function replaces the Excel-based tissue data loading with SSM file processing,
    implementing Task 3.1 from the development roadmap.
    
    Args:
        ssm_file: Path to SSM file containing tissue mutation data
        logger: Logger instance for reporting
        
    Returns:
        Tuple of (tissue_dataframe, gene2idx_mapping, gene_name_list)
    """
    logger.info(f"Loading tissue data from SSM file: {ssm_file}")
    
    # Read SSM file
    try:
        ssm_df = pd.read_csv(ssm_file, sep='\t')
        logger.info(f"SSM file loaded: {ssm_df.shape[0]} mutations, {ssm_df.shape[1]} columns")
    except Exception as e:
        logger.error(f"Error reading SSM file: {e}")
        raise
    
    # Validate SSM file format
    required_columns = ['id', 'gene', 'a', 'd', 'mu_r', 'mu_v']
    missing_columns = [col for col in required_columns if col not in ssm_df.columns]
    if missing_columns:
        logger.error(f"Missing required columns in SSM file: {missing_columns}")
        raise ValueError(f"Invalid SSM file format. Missing columns: {missing_columns}")
    
    # Process tissue data
    tissue_df = ssm_df.copy()
    
    # Create gene list and mapping from tissue data
    gene_list = [f's{idx}' for idx in range(len(tissue_df))]  # Format as 's0', 's1', etc.
    gene2idx = {gene_id: idx for idx, gene_id in enumerate(gene_list)}
    
    # Process gene names with duplicate handling (matching original logic)
    gene_name_list = []
    gene_count = {}
    
    for i in range(tissue_df.shape[0]):
        gene = tissue_df.iloc[i]['gene']  # Get gene name
        
        # Handle duplicate gene names
        if gene in gene_name_list:
            gene_count[gene] += 1
            gene = f"{gene}_{gene_count[gene]}"
        else:
            gene_count[gene] = 1
        
        # Handle non-string gene names (use genomic location if available)
        if not isinstance(gene, str):
            # Use ID as fallback
            gene = f"unknown_{tissue_df.iloc[i]['id']}"
        
        gene_name_list.append(gene)
    
    logger.info(f"Created gene list: {len(gene_list)} genes in 's0', 's1'... format")
    logger.info(f"Processed gene names: {len(gene_name_list)} names with duplicate handling")
    
    return tissue_df, gene2idx, gene_name_list


def load_longitudinal_data_from_csv(csv_file: Path, logger: logging.Logger) -> Dict[str, pd.DataFrame]:
    """
    Load and process longitudinal ddPCR data from CSV format.
    
    This function implements Task 3.2 from the development roadmap, replacing
    Excel-based longitudinal data with CSV processing.
    
    Args:
        csv_file: Path to CSV file containing longitudinal ddPCR data
        logger: Logger instance for reporting
        
    Returns:
        Dictionary mapping timepoint dates to ddPCR DataFrames
    """
    logger.info(f"Loading longitudinal data from CSV file: {csv_file}")
    
    try:
        # Read CSV file
        longitudinal_df = pd.read_csv(csv_file)
        logger.info(f"Longitudinal CSV loaded: {longitudinal_df.shape[0]} rows, {longitudinal_df.shape[1]} columns")
        
        # Validate required columns
        required_columns = ['date', 'gene', 'mutant_droplets', 'total_droplets']
        missing_columns = [col for col in required_columns if col not in longitudinal_df.columns]
        if missing_columns:
            logger.error(f"Missing required columns in longitudinal CSV: {missing_columns}")
            raise ValueError(f"Invalid CSV format. Missing columns: {missing_columns}")
        
        # Group data by date/timepoint
        timepoint_data = {}
        unique_dates = sorted(longitudinal_df['date'].unique())
        logger.info(f"Found {len(unique_dates)} unique timepoints: {unique_dates}")
        
        for date in unique_dates:
            # Filter data for this timepoint
            timepoint_df = longitudinal_df[longitudinal_df['date'] == date].copy()
            
            # Create ddPCR-compatible format
            ddpcr_df = timepoint_df.set_index('gene')
            ddpcr_df['MutDOR'] = ddpcr_df['mutant_droplets']  # Mutant droplet count
            ddpcr_df['DOR'] = ddpcr_df['total_droplets']      # Total droplet count
            
            timepoint_data[date] = ddpcr_df
            logger.info(f"Processed timepoint {date}: {len(ddpcr_df)} markers")
        
        return timepoint_data
        
    except Exception as e:
        logger.error(f"Error processing longitudinal CSV file: {e}")
        raise


def main():
    """
    Main entry point for the longitudinal analysis pipeline.
    """
    # Parse command line arguments
    args = parse_args()
    
    # Set up output directory and logging
    output_dir = Path(args.output_dir)
    logger = setup_logging(output_dir, args.patient_id)
    
    try:
        # Validate input files
        if not validate_input_files(args, logger):
            logger.error("Input validation failed. Exiting.")
            sys.exit(1)
        
        # Load tree distribution data from aggregation stage
        aggregation_dir = Path(args.aggregation_dir)
        tree_distribution_summary, tree_distribution_full = load_tree_distributions(
            aggregation_dir, args.method, logger)
        
        # Load tissue data from SSM file (Task 3.1)
        ssm_file = Path(args.ssm_file)
        tissue_df, gene2idx, gene_name_list = load_tissue_data_from_ssm(ssm_file, logger)
        
        # Load longitudinal data from CSV file (Task 3.2)  
        longitudinal_file = Path(args.longitudinal_data)
        timepoint_data = load_longitudinal_data_from_csv(longitudinal_file, logger)
        
        # Log successful data loading
        logger.info("Data loading completed successfully")
        logger.info(f"Tree distributions: {len(tree_distribution_summary['tree_structure'])} trees")
        logger.info(f"Tissue mutations: {len(tissue_df)} mutations")
        logger.info(f"Longitudinal timepoints: {len(timepoint_data)} timepoints")
        
        # Create output subdirectories
        output_dir.mkdir(parents=True, exist_ok=True)
        updated_trees_dir = output_dir / 'updated_trees'
        marker_selections_dir = output_dir / 'marker_selections'
        plots_dir = output_dir / 'plots'
        
        updated_trees_dir.mkdir(exist_ok=True)
        marker_selections_dir.mkdir(exist_ok=True)
        if not args.no_plots:
            plots_dir.mkdir(exist_ok=True)
        
        logger.info("Starting iterative Bayesian analysis workflow...")
        
        # Sort timepoints chronologically
        sorted_timepoints = sorted(timepoint_data.keys())
        logger.info(f"Processing timepoints in order: {sorted_timepoints}")
        
        # Process each timepoint sequentially
        for order_idx, timepoint in enumerate(sorted_timepoints):
            logger.info(f"Processing timepoint {order_idx + 1}/{len(sorted_timepoints)}: {timepoint}")
            
            # For the first timepoint, use original tree distributions
            if order_idx == 0:
                current_tree_summary = tree_distribution_summary
                current_tree_full = tree_distribution_full
                
                # Extract tree components for analysis
                tree_list = current_tree_summary['tree_structure']
                node_list = current_tree_summary['node_dict']
                tree_freq_list = current_tree_summary['freq']
                clonal_freq_list = current_tree_full['vaf_frac']
                
                logger.info(f"Using original tree distributions: {len(tree_list)} trees")
            
            # For subsequent timepoints, load updated tree distribution from previous iteration
            else:
                updated_file = updated_trees_dir / f'{args.method}_bootstrap_summary_updated_{args.algorithm}_{args.n_markers}_{order_idx-1}_bayesian.pkl'
                
                if not updated_file.exists():
                    logger.error(f"Updated tree distribution file not found: {updated_file}")
                    raise FileNotFoundError(f"Missing updated tree distribution for timepoint {order_idx-1}")
                
                with open(updated_file, 'rb') as f:
                    current_tree_summary = pickle.load(f)
                
                # Extract tree components
                tree_list = current_tree_summary['tree_structure']
                node_list = current_tree_summary['node_dict']
                tree_freq_list = current_tree_summary['freq']
                
                # Recalculate clonal frequencies by averaging across samples
                clonal_freq_list = []
                for idx in range(len(current_tree_summary['vaf_frac'])):
                    clonal_freq_dict = current_tree_summary['vaf_frac'][idx]
                    clonal_freq_dict_new = {}
                    for node, freqs in clonal_freq_dict.items():
                        clonal_freq_dict_new[node] = [list(np.array(freqs).mean(axis=0))]
                    clonal_freq_list.append(clonal_freq_dict_new)
                
                logger.info(f"Using updated tree distributions from previous timepoint: {len(tree_list)} trees")
            
            # Select optimal markers based on current tree structure
            logger.info(f"Selecting {args.n_markers} optimal markers for timepoint {timepoint}")
            
            selected_markers, obj_frac, obj_struct = select_markers_tree_gp(
                gene_list, args.n_markers, tree_list, node_list, clonal_freq_list,
                gene2idx, tree_freq_list, read_depth=args.read_depth,
                lam1=args.lambda1, lam2=args.lambda2, focus_sample_idx=args.focus_sample)
            
            # Convert selected marker IDs to gene names (matching original logic)
            selected_gene_names = [gene_name_list[int(marker_id[1:])] for marker_id in selected_markers]
            
            logger.info(f"Selected markers: {selected_markers}")
            logger.info(f"Selected gene names: {selected_gene_names}")
            
            # Get ddPCR data for current timepoint
            current_ddpcr_data = timepoint_data[timepoint]
            
            # Extract ddPCR measurements for selected markers (matching original format)
            ddpcr_measurements = []
            for gene_name in selected_gene_names:
                if gene_name in current_ddpcr_data.index:
                    mut_count = current_ddpcr_data.loc[gene_name, 'MutDOR']  # Mutant droplets
                    total_count = current_ddpcr_data.loc[gene_name, 'DOR']   # Total droplets
                    wt_count = total_count - mut_count  # Calculate WT count
                    
                    ddpcr_measurements.append({
                        'gene': gene_name,
                        'mut': mut_count,
                        'WT': wt_count,
                        'liquid_biopsy_sample': timepoint
                    })
                else:
                    logger.warning(f"Selected marker {gene_name} not found in ddPCR data for timepoint {timepoint}")
            
            if not ddpcr_measurements:
                logger.error(f"No ddPCR data found for selected markers at timepoint {timepoint}")
                continue
            
            # Create DataFrame with ddPCR measurements (matching original format)
            df_ddpcr = pd.DataFrame(ddpcr_measurements)
            marker_idx2gene = {i: df_ddpcr["gene"].iloc[i] for i in range(len(df_ddpcr))}
            
            # Extract counts for Bayesian updating (matching original calculation)
            ddpcr_marker_counts = list(df_ddpcr["mut"])
            read_depth_list = list(df_ddpcr["mut"] + df_ddpcr["WT"])  # Total = mut + WT
            
            logger.info(f"ddPCR measurements: {len(ddpcr_measurements)} markers")
            logger.info(f"Mutant counts: {ddpcr_marker_counts}")
            logger.info(f"Read depths: {read_depth_list}")
            
            # Extract tree information from summary (matching original)
            tree_list_summary, node_list_summary, node_name_list_summary, tree_freq_list_summary = \
                current_tree_summary['tree_structure'], current_tree_summary['node_dict'], \
                current_tree_summary['node_dict_name'], current_tree_summary['freq']
            
            # Update tree distributions using Bayesian approach
            logger.info("Updating tree distributions using Bayesian inference...")
            
            updated_tree_freq_list = adjust_tree_distribution_struct_bayesian(
                tree_list_summary, node_name_list_summary,
                tree_freq_list_summary, read_depth_list,
                ddpcr_marker_counts, marker_idx2gene)
            
            # Create updated tree distribution summary
            updated_tree_distribution_summary = update_tree_distribution_bayesian(
                current_tree_summary, updated_tree_freq_list)
            
            # Save updated tree distribution for next iteration
            updated_file = updated_trees_dir / f'{args.method}_bootstrap_summary_updated_{args.algorithm}_{args.n_markers}_{order_idx}_bayesian.pkl'
            with open(updated_file, 'wb') as f:
                pickle.dump(updated_tree_distribution_summary, f)
            
            logger.info(f"Saved updated tree distribution: {updated_file}")
            
            # Save marker selection results
            marker_selection_results = {
                'timepoint': timepoint,
                'order_idx': order_idx,
                'selected_markers': selected_markers,
                'selected_gene_names': selected_gene_names,
                'ddpcr_measurements': ddpcr_measurements,
                'objective_fraction': obj_frac,
                'objective_structure': obj_struct,
                'parameters': {
                    'n_markers': args.n_markers,
                    'read_depth': args.read_depth,
                    'algorithm': args.algorithm,
                    'lambda1': args.lambda1,
                    'lambda2': args.lambda2
                }
            }
            
            marker_file = marker_selections_dir / f'marker_selection_{timepoint}_{order_idx}.json'
            with open(marker_file, 'w') as f:
                json.dump(marker_selection_results, f, indent=2, default=str)
            
            logger.info(f"Saved marker selection results: {marker_file}")
            
            # Save intermediate results if requested
            if args.save_intermediate:
                intermediate_dir = output_dir / 'intermediate' / f'timepoint_{order_idx}_{timepoint}'
                intermediate_dir.mkdir(parents=True, exist_ok=True)
                
                # Save cleaned data structures
                with open(intermediate_dir / 'node_list_scrub.pkl', 'wb') as f:
                    pickle.dump(node_list_scrub, f)
                with open(intermediate_dir / 'clonal_freq_list_scrub.pkl', 'wb') as f:
                    pickle.dump(clonal_freq_list_scrub, f)
                
                logger.info(f"Saved intermediate results: {intermediate_dir}")
        
        # Generate summary report
        summary_report = {
            'patient_id': args.patient_id,
            'analysis_timestamp': datetime.now().isoformat(),
            'parameters': {
                'n_markers': args.n_markers,
                'read_depth': args.read_depth,
                'algorithm': args.algorithm,
                'method': args.method,
                'lambda1': args.lambda1,
                'lambda2': args.lambda2
            },
            'input_files': {
                'aggregation_dir': str(args.aggregation_dir),
                'ssm_file': str(args.ssm_file),
                'longitudinal_data': str(args.longitudinal_data)
            },
            'results': {
                'total_timepoints': len(sorted_timepoints),
                'timepoints_processed': sorted_timepoints,
                'output_directory': str(output_dir)
            }
        }
        
        summary_file = output_dir / 'analysis_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary_report, f, indent=2)
        
        logger.info(f"Analysis completed successfully for {len(sorted_timepoints)} timepoints")
        logger.info(f"Results saved to: {output_dir}")
        logger.info(f"Summary report: {summary_file}")
        
        logger.info("Longitudinal analysis pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}")
        if args.debug:
            import traceback
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
        sys.exit(1)


if __name__ == '__main__':
    main() 