#!/usr/bin/env python3
"""
Longitudinal visualization module for cancer evolution analysis.

This module provides clean, simple visualization functions for both
dynamic and fixed marker analysis modes as specified in the todo.md:

1. Phylogenetic Tree(s) - for both modes
2. Tree Evolution Plots - showing weight changes over time
3. VAF Plots (Fixed Mode) - display chosen marker VAFs
4. VAF Plots (Dynamic Mode) - display final converged marker VAFs

Authors: TracerX Pipeline Development Team
Version: 2.0.0
"""

import logging
import json
import pickle
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from graphviz import Digraph

# Import existing visualization utilities from the pipeline
from visualize import render_tumor_tree, root_searching

logger = logging.getLogger(__name__)


def create_visualization_plots(analysis_mode: str, patient_id: str, output_dir: Path, 
                             results_summary: Dict, timepoint_data: Dict, 
                             logger: logging.Logger) -> Dict[str, str]:
    """
    Create all required visualization plots for longitudinal analysis.
    
    Args:
        analysis_mode: 'fixed' or 'dynamic'
        patient_id: Patient identifier
        output_dir: Output directory for plots
        results_summary: Analysis results summary
        timepoint_data: Timepoint data dictionary
        logger: Logger instance
        
    Returns:
        Dictionary mapping plot types to file paths
    """
    logger.info(f"Creating visualization plots for {analysis_mode} analysis")
    
    # Create visualization directory
    viz_dir = output_dir / f'{analysis_mode}_marker_analysis' / 'visualizations'
    viz_dir.mkdir(parents=True, exist_ok=True)
    
    plot_files = {}
    
    try:
        # 1. Phylogenetic Tree(s) - for both modes
        tree_plot = create_phylogenetic_tree_plot(
            analysis_mode, patient_id, viz_dir, results_summary, logger)
        plot_files['phylogenetic_tree'] = tree_plot
        
        # 2. Tree Evolution Plots - for both modes
        evolution_plot = create_tree_evolution_plot(
            analysis_mode, patient_id, viz_dir, results_summary, output_dir, logger)
        plot_files['tree_evolution'] = evolution_plot
        
        # 3. VAF Plots - mode-specific
        vaf_plot = create_vaf_plots(
            analysis_mode, patient_id, viz_dir, results_summary, timepoint_data, logger)
        plot_files['vaf_plots'] = vaf_plot
        
        logger.info(f"Successfully created all visualization plots")
        logger.info(f"Plots saved in: {viz_dir}")
        
    except Exception as e:
        logger.error(f"Error creating visualization plots: {e}")
        raise
    
    return plot_files


def create_phylogenetic_tree_plot(analysis_mode: str, patient_id: str, viz_dir: Path,
                                 results_summary: Dict, logger: logging.Logger) -> Optional[str]:
    """
    Create phylogenetic tree visualization(s).
    
    Shows the best/converged phylogenetic tree(s) from the analysis.
    References the existing tree rendering approach from steps 1-4.
    """
    logger.info("Creating phylogenetic tree plot")
    
    try:
        # Load the final tree distribution
        final_tree_file = results_summary.get('final_tree_distribution_file')
        if not final_tree_file or not Path(final_tree_file).exists():
            logger.warning(f"Final tree distribution file not found: {final_tree_file}")
            return None
        
        with open(final_tree_file, 'rb') as f:
            final_tree_distribution = pickle.load(f)
        
        # Find the best tree (highest frequency)
        tree_frequencies = final_tree_distribution['freq']
        best_tree_idx = np.argmax(tree_frequencies)
        best_frequency = tree_frequencies[best_tree_idx]
        
        # Extract tree data for the best tree
        tree_structure = final_tree_distribution['tree_structure'][best_tree_idx]
        node_dict_name = final_tree_distribution['node_dict_name'][best_tree_idx]
        
        logger.info(f"Best tree: index {best_tree_idx}, frequency {best_frequency:.3f}")
        
        # Generate phylogenetic tree using existing render_tumor_tree function
        # (following reference from steps 1-4 styling)
        g = render_tumor_tree(tree_structure, node_dict_name)
        
        # Save the tree plot
        tree_filename = viz_dir / f'{patient_id}_{analysis_mode}_phylogenetic_tree'
        g.render(filename=tree_filename, format='png', cleanup=True)
        
        tree_plot_path = f"{tree_filename}.png"
        logger.info(f"Saved phylogenetic tree plot: {tree_plot_path}")
        
        return tree_plot_path
        
    except Exception as e:
        logger.error(f"Error creating phylogenetic tree plot: {e}")
        return None


def create_tree_evolution_plot(analysis_mode: str, patient_id: str, viz_dir: Path,
                              results_summary: Dict, output_dir: Path, logger: logging.Logger) -> Optional[str]:
    """
    Create tree evolution plots showing how tree weights change over time.
    
    Shows convergence behavior and weight dynamics during the optimization process.
    """
    logger.info("Creating tree evolution plot")
    
    try:
        # Load tree distributions from all timepoints
        trees_dir = output_dir / f'{analysis_mode}_marker_analysis' / 'updated_trees'
        
        if not trees_dir.exists():
            logger.warning(f"Updated trees directory not found: {trees_dir}")
            return None
        
        # Find all timepoint files
        timepoint_files = sorted(trees_dir.glob('*timepoint_*.pkl'))
        
        if not timepoint_files:
            logger.warning(f"No timepoint tree files found in {trees_dir}")
            return None
        
        # Load tree frequencies for each timepoint
        timepoints = []
        all_tree_frequencies = []
        
        # Load initial tree distribution (timepoint 0)
        initial_file = None
        for f in timepoint_files:
            if 'timepoint_0' in f.name:
                initial_file = f
                break
        
        if initial_file:
            with open(initial_file, 'rb') as f:
                initial_tree = pickle.load(f)
            timepoints.append(0)
            all_tree_frequencies.append(initial_tree['freq'])
        
        # Load subsequent timepoints
        for i, tree_file in enumerate(timepoint_files[1:], 1):
            try:
                with open(tree_file, 'rb') as f:
                    tree_dist = pickle.load(f)
                timepoints.append(i)
                all_tree_frequencies.append(tree_dist['freq'])
            except Exception as e:
                logger.warning(f"Could not load {tree_file}: {e}")
                continue
        
        if len(timepoints) < 2:
            logger.warning("Insufficient timepoint data for evolution plot")
            return None
        
        # Create the evolution plot
        plt.figure(figsize=(12, 8))
        
        # Find trees with meaningful frequencies (>1%)
        n_trees = len(all_tree_frequencies[0])
        for tree_idx in range(n_trees):
            tree_freqs_over_time = [freqs[tree_idx] for freqs in all_tree_frequencies]
            
            # Only plot trees that have significant frequency at some point
            if max(tree_freqs_over_time) > 0.01:  # 1% threshold
                # Color by whether frequency increases or decreases
                final_freq = tree_freqs_over_time[-1]
                initial_freq = tree_freqs_over_time[0]
                
                if final_freq > initial_freq:
                    color = "tab:orange"  # Increasing frequency
                    alpha = 0.8
                else:
                    color = "tab:blue"   # Decreasing frequency
                    alpha = 0.6
                
                plt.plot(timepoints, tree_freqs_over_time, 
                        marker='o', linestyle='-', color=color, 
                        alpha=alpha, markersize=4, linewidth=2,
                        label=f'Tree {tree_idx}' if tree_idx < 5 else "")
        
        # Customize the plot
        plt.xlabel('Timepoint', fontweight='bold', fontsize=12)
        plt.ylabel('Tree Weight/Frequency', fontweight='bold', fontsize=12)
        plt.title(f'{patient_id} - Tree Evolution Over Time ({analysis_mode.title()} Analysis)',
                 fontsize=14, fontweight='bold')
        
        # Add grid for better readability
        plt.grid(True, alpha=0.3)
        
        # Add legend for first few trees only (to avoid clutter)
        if n_trees <= 5:
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Set x-axis to show integer timepoints
        plt.xticks(timepoints)
        plt.xlim(-0.1, max(timepoints) + 0.1)
        plt.ylim(0, 1.05)
        
        # Save the plot
        evolution_plot_path = viz_dir / f'{patient_id}_{analysis_mode}_tree_evolution.png'
        plt.tight_layout()
        plt.savefig(evolution_plot_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        logger.info(f"Saved tree evolution plot: {evolution_plot_path}")
        return str(evolution_plot_path)
        
    except Exception as e:
        logger.error(f"Error creating tree evolution plot: {e}")
        return None


def create_vaf_plots(analysis_mode: str, patient_id: str, viz_dir: Path,
                    results_summary: Dict, timepoint_data: Dict, logger: logging.Logger) -> Optional[str]:
    """
    Create VAF (Variant Allele Frequency) plots.
    
    For fixed mode: Display VAF plots of the CHOSEN markers
    For dynamic mode: Display VAF plots of the final, best, converged markers
    """
    logger.info(f"Creating VAF plots for {analysis_mode} mode")
    
    try:
        if analysis_mode == 'fixed':
            return create_fixed_marker_vaf_plots(patient_id, viz_dir, results_summary, timepoint_data, logger)
        elif analysis_mode == 'dynamic':
            return create_dynamic_marker_vaf_plots(patient_id, viz_dir, results_summary, timepoint_data, logger)
        else:
            logger.error(f"Unknown analysis mode: {analysis_mode}")
            return None
            
    except Exception as e:
        logger.error(f"Error creating VAF plots: {e}")
        return None


def create_fixed_marker_vaf_plots(patient_id: str, viz_dir: Path, results_summary: Dict,
                                 timepoint_data: Dict, logger: logging.Logger) -> Optional[str]:
    """
    Create VAF plots for fixed marker analysis showing the chosen markers.
    """
    logger.info("Creating VAF plots for fixed markers")
    
    try:
        # Get fixed markers from analysis summary
        analysis_summary = results_summary.get('analysis_summary', {})
        fixed_gene_names = analysis_summary.get('fixed_gene_names', [])
        
        if not fixed_gene_names:
            logger.warning("No fixed gene names found in results summary")
            return None
        
        # Collect VAF data across timepoints
        vaf_data = []
        sorted_timepoints = sorted(timepoint_data.keys())
        
        for timepoint in sorted_timepoints:
            timepoint_df = timepoint_data[timepoint]
            
            for gene_name in fixed_gene_names:
                if gene_name in timepoint_df.index:
                    mut_count = timepoint_df.loc[gene_name, 'MutDOR']
                    total_count = timepoint_df.loc[gene_name, 'DOR']
                    vaf = mut_count / total_count if total_count > 0 else 0
                    
                    vaf_data.append({
                        'timepoint': timepoint,
                        'marker': gene_name,
                        'vaf': vaf,
                        'mut_count': mut_count,
                        'total_count': total_count
                    })
        
        if not vaf_data:
            logger.warning("No VAF data collected for fixed markers")
            return None
        
        # Create VAF plot
        df_vaf = pd.DataFrame(vaf_data)
        
        plt.figure(figsize=(12, 8))
        
        # Use different colors for each marker
        n_markers = len(fixed_gene_names)
        colors = sns.color_palette("Set2", n_markers)
        
        for i, marker in enumerate(fixed_gene_names):
            marker_data = df_vaf[df_vaf['marker'] == marker]
            if not marker_data.empty:
                plt.plot(marker_data['timepoint'], marker_data['vaf'], 
                        marker='o', linestyle='-', color=colors[i], 
                        markersize=6, linewidth=2, label=marker)
        
        # Customize the plot
        plt.xlabel('Timepoint', fontweight='bold', fontsize=12)
        plt.ylabel('VAF (Variant Allele Frequency)', fontweight='bold', fontsize=12)
        plt.title(f'{patient_id} - Fixed Marker VAF Over Time',
                 fontsize=14, fontweight='bold')
        
        # Format timepoint labels (rotate if many)
        if len(sorted_timepoints) > 6:
            plt.xticks(rotation=45)
        
        plt.grid(True, alpha=0.3)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.ylim(0, max(df_vaf['vaf']) * 1.1)
        
        # Save the plot
        vaf_plot_path = viz_dir / f'{patient_id}_fixed_marker_vaf.png'
        plt.tight_layout()
        plt.savefig(vaf_plot_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        logger.info(f"Saved fixed marker VAF plot: {vaf_plot_path}")
        return str(vaf_plot_path)
        
    except Exception as e:
        logger.error(f"Error creating fixed marker VAF plots: {e}")
        return None


def create_dynamic_marker_vaf_plots(patient_id: str, viz_dir: Path, results_summary: Dict,
                                   timepoint_data: Dict, logger: logging.Logger) -> Optional[str]:
    """
    Create VAF plots for dynamic marker analysis showing the final converged markers.
    """
    logger.info("Creating VAF plots for dynamic markers")
    
    try:
        # Get marker selections from all timepoints
        all_marker_selections = results_summary.get('all_marker_selections', [])
        
        if not all_marker_selections:
            logger.warning("No marker selections found in results summary")
            return None
        
        # Get the final timepoint marker selection (the "converged" markers)
        final_selection = all_marker_selections[-1]
        final_markers = final_selection.get('selected_gene_names', [])
        
        if not final_markers:
            logger.warning("No final markers found in dynamic analysis")
            return None
        
        logger.info(f"Using final converged markers: {final_markers}")
        
        # Collect VAF data for final markers across all timepoints where they were measured
        vaf_data = []
        
        for selection in all_marker_selections:
            timepoint = selection['timepoint']
            selected_markers = selection.get('selected_gene_names', [])
            ddpcr_measurements = selection.get('ddpcr_measurements', [])
            
            # Only include final markers that were actually measured
            for measurement in ddpcr_measurements:
                gene_name = measurement['gene']
                if gene_name in final_markers:
                    mut_count = measurement['mut']
                    total_count = mut_count + measurement['WT']
                    vaf = mut_count / total_count if total_count > 0 else 0
                    
                    vaf_data.append({
                        'timepoint': timepoint,
                        'marker': gene_name,
                        'vaf': vaf,
                        'mut_count': mut_count,
                        'total_count': total_count
                    })
        
        if not vaf_data:
            logger.warning("No VAF data collected for dynamic markers")
            return None
        
        # Create VAF plot
        df_vaf = pd.DataFrame(vaf_data)
        
        plt.figure(figsize=(12, 8))
        
        # Use different colors for each marker
        unique_markers = df_vaf['marker'].unique()
        n_markers = len(unique_markers)
        colors = sns.color_palette("Set2", n_markers)
        
        for i, marker in enumerate(unique_markers):
            marker_data = df_vaf[df_vaf['marker'] == marker]
            if not marker_data.empty:
                plt.plot(marker_data['timepoint'], marker_data['vaf'], 
                        marker='o', linestyle='-', color=colors[i], 
                        markersize=6, linewidth=2, label=marker)
        
        # Customize the plot
        plt.xlabel('Timepoint', fontweight='bold', fontsize=12)
        plt.ylabel('VAF (Variant Allele Frequency)', fontweight='bold', fontsize=12)
        plt.title(f'{patient_id} - Dynamic Marker VAF Over Time (Final Converged Markers)',
                 fontsize=14, fontweight='bold')
        
        # Format timepoint labels (rotate if many)
        timepoints = sorted(df_vaf['timepoint'].unique())
        if len(timepoints) > 6:
            plt.xticks(rotation=45)
        
        plt.grid(True, alpha=0.3)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.ylim(0, max(df_vaf['vaf']) * 1.1)
        
        # Save the plot
        vaf_plot_path = viz_dir / f'{patient_id}_dynamic_marker_vaf.png'
        plt.tight_layout()
        plt.savefig(vaf_plot_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        logger.info(f"Saved dynamic marker VAF plot: {vaf_plot_path}")
        return str(vaf_plot_path)
        
    except Exception as e:
        logger.error(f"Error creating dynamic marker VAF plots: {e}")
        return None


def save_visualization_summary(viz_dir: Path, plot_files: Dict[str, str], 
                              analysis_mode: str, patient_id: str) -> Path:
    """
    Save a summary of all generated visualization files.
    
    Args:
        viz_dir: Visualization directory
        plot_files: Dictionary of plot types to file paths
        analysis_mode: Analysis mode
        patient_id: Patient identifier
        
    Returns:
        Path to summary file
    """
    summary_data = {
        'patient_id': patient_id,
        'analysis_mode': analysis_mode,
        'visualization_files': plot_files,
        'description': {
            'phylogenetic_tree': 'Best/converged phylogenetic tree from analysis',
            'tree_evolution': 'Tree weight changes over time showing convergence',
            'vaf_plots': f'VAF plots for {analysis_mode} markers over time'
        }
    }
    
    summary_file = viz_dir / 'visualization_summary.json'
    with open(summary_file, 'w') as f:
        json.dump(summary_data, f, indent=2, default=str)
    
    return summary_file