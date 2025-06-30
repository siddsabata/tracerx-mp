# TracerX Marker Selection Pipeline - Visualization Plan

## Overview
Updated visualization plan for both **dynamic** and **fixed** marker selection modes.
All plots should be clean, simple, easy to read, and saved as PNG files.

## Required Plots

### 1. Phylogenetic Tree(s) 
**For both dynamic and fixed modes**
- Display the best, converged phylogenetic tree(s)
- Usually 1 tree, but could be multiple trees
- Reference steps 1-4 for styling and implementation approach
- Save as PNG format

### 2. Tree Evolution Plots
**For both dynamic and fixed modes**
- Show how tree weights change over time during the optimization process
- Track convergence behavior and weight dynamics
- Clean, simple line plots showing progression
- Save as PNG format

### 3a. VAF Plots (Fixed Marker Mode)
**For fixed marker mode only**
- Display VAF (Variant Allele Frequency) plots of the CHOSEN markers
- Show the specific markers that were pre-selected for analysis
- Save as PNG format

### 3b. VAF Plots (Dynamic Marker Mode)  
**For dynamic marker mode only**
- Display VAF plots of the final, best, converged markers
- Show the markers that were selected through the dynamic optimization process
- Save as PNG format

## Implementation Guidelines

- **Simplicity**: Implement in the simplest possible way
- **Reference**: Use steps 1-4 as reference for phylogenetic tree plots and styling
- **Consistency**: Maintain clean, consistent visual style across all plots
- **Format**: All plots saved as PNG files
- **Readability**: Ensure plots are easy to read and interpret

## Notes
- This replaces the previous plotting approach from steps 1-4
- Focus on core functionality and clean visualization
- Keep implementation modular and well-documented
