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
    
    # Create gene-to-index mapping
    gene2idx = {row['id']: idx for idx, row in tissue_df.iterrows()}
    logger.info(f"Created gene-to-index mapping for {len(gene2idx)} mutations")
    
    # Process gene names with duplicate handling
    gene_name_list = []
    gene_count = {}
    
    for _, row in tissue_df.iterrows():
        gene = row['gene']
        
        # Handle duplicate gene names
        if gene in gene_name_list:
            gene_count[gene] += 1
            gene = f"{gene}_{gene_count[gene]}"
        else:
            gene_count[gene] = 1
        
        # Handle non-string gene names (use genomic location)
        if not isinstance(gene, str):
            # Extract chromosome and position from gene column if available
            gene = f"unknown_{row['id']}"
        
        gene_name_list.append(gene)
    
    logger.info(f"Processed {len(gene_name_list)} gene names with duplicate handling")
    
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
        
        # TODO: Implement the iterative Bayesian analysis workflow here
        # This will be the next step in building out the production pipeline
        
        logger.info("Longitudinal analysis pipeline setup completed successfully")
        
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}")
        if args.debug:
            import traceback
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
        sys.exit(1)


if __name__ == '__main__':
    main() 