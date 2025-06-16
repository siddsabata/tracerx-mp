# Longitudinal Tumor Evolution Analysis Pipeline
## Implementation Plan & Developer Guide

### Table of Contents
1. [Project Overview](#project-overview)
2. [Scientific Background](#scientific-background)
3. [System Architecture](#system-architecture)
4. [Implementation Strategy](#implementation-strategy)
5. [Development Tickets](#development-tickets)
6. [Technical Specifications](#technical-specifications)
7. [Testing Strategy](#testing-strategy)

---

## Project Overview

### Goal
Complete the HPC longitudinal analysis pipeline to support both dynamic and fixed marker tracking approaches for tumor evolution analysis. The pipeline will generate comprehensive figures (PNG/PDF) and structured metrics (JSON) for downstream analysis and clinical interpretation.

### Current State
- ✅ Basic HPC pipeline for longitudinal analysis exists (`5-long/longitudinal_update.py`)
- ✅ Dynamic marker selection optimization is functional
- ✅ **Fixed marker functionality implemented**: Complete fixed marker selection and tracking
- ✅ **Command line interface enhanced**: Support for both dynamic and fixed approaches
- ✅ **Production SLURM scripts created**: Both dynamic and fixed marker analysis modes
- ✅ **YAML configuration system implemented**: Complete migration from command-line arguments
- ✅ **Technical stability achieved**: Marker validation and numerical overflow fixes resolved
- ⏳ **Figure generation needed**: Automatic generation of key analysis plots
- ⏳ **Structured output needed**: Comprehensive JSON metrics and metadata
- ⏳ **Enhanced visualization needed**: Time series plots and comparative analysis

### Target Deliverable
A complete HPC pipeline that:
1. ✅ **Processes both approaches**: Dynamic marker selection and fixed marker tracking
2. ✅ **YAML configuration support**: Robust configuration management with validation
3. ✅ **Technical robustness**: Resolved marker validation and numerical stability issues
4. **Generates publication-ready figures**: PNG/PDF plots for all key analyses
5. **Outputs structured metrics**: JSON files with comprehensive analysis results
6. **Provides comparative analysis**: Performance comparison between approaches
7. ✅ **Runs autonomously**: Complete analysis from initial data to final outputs

The pipeline now supports:
- **Dynamic Mode**: `--config configs/dynamic_analysis.yaml` or `--analysis-mode dynamic`
- **Fixed Mode**: `--config configs/fixed_analysis.yaml` or `--analysis-mode fixed --fixed-markers GENE1 GENE2`
- **Comparative Mode**: `--analysis-mode both` for direct comparison
- **Clinical Integration**: User-specified markers for standardized clinical workflows
- **Production Deployment**: SLURM scripts with YAML configuration support
- **Technical Stability**: Resolved marker validation bugs and numerical overflow issues

### Recent Major Achievements ✅ **COMPLETED**

#### YAML Configuration System Implementation
- ✅ **Complete migration**: From complex command-line arguments to structured YAML files
- ✅ **Shell parsing resolution**: Fixed truncation of mutation names containing `>` characters
- ✅ **Configuration validation**: Robust loading with comprehensive error handling
- ✅ **Template creation**: Production-ready configurations for different scenarios
- ✅ **Backward compatibility**: Maintained support for legacy command-line interface

#### Marker Validation System Fixes
- ✅ **Critical bug resolution**: Fixed `gene2idx` mapping that prevented marker identification
- ✅ **Validation enhancement**: Proper mapping from gene names to indices
- ✅ **Error handling**: Graceful handling of missing markers with clear feedback
- ✅ **Clinical compatibility**: Validated with real gene identifiers

#### Numerical Stability Improvements
- ✅ **Overflow protection**: Implemented log-space arithmetic for large read depths (60,000+)
- ✅ **Robust computation**: Used `scipy.special.gammaln` for binomial coefficients
- ✅ **Fallback strategies**: Multiple computational approaches for edge cases
- ✅ **Integration stability**: Enhanced numerical integration with improved tolerances

#### Enhanced Error Handling and Logging
- ✅ **Logger initialization**: Fixed UnboundLocalError in exception handling
- ✅ **Early setup**: Logger available throughout pipeline execution
- ✅ **Comprehensive validation**: Configuration file validation with meaningful errors
- ✅ **Debug support**: Enhanced debugging capabilities for troubleshooting

---

## Scientific Background

### What is Tumor Evolution Tracking?
Tumors evolve over time, acquiring new mutations and changing their clonal composition. By tracking specific genetic markers in liquid biopsies (blood samples), we can monitor this evolution non-invasively.

### Phylogenetic Trees in Cancer
- **Nodes**: Represent clonal populations with specific mutations
- **Edges**: Show evolutionary relationships (parent-child clones)
- **Frequencies**: Indicate the proportion of each clone in the tumor
- **VAF (Variant Allele Frequency)**: Percentage of DNA molecules carrying a specific mutation

### Two Clinical Paradigms

#### 1. Dynamic Marker Selection (Scientific Approach)
**Philosophy**: Optimize marker selection at each timepoint based on current tumor state.

**Process**:
1. At each timepoint, analyze current tree distribution
2. Use optimization algorithms (Gurobi) to select best markers for tracking
3. Update tree probabilities using Bayesian inference with new measurements
4. Repeat for next timepoint with updated tree knowledge

**Advantages**:
- Maximizes information gain at each step
- Adapts to tumor evolution dynamics
- Provides insights into methodological performance

**Use Case**: Research studies, method development, understanding tumor dynamics

#### 2. Fixed Marker Tracking (Clinical Approach)
**Philosophy**: Select optimal markers once and track them consistently over time.

**Process**:
1. Use initial tumor analysis to select best N markers
2. Track these same markers at all subsequent timepoints
3. Monitor VAF changes over time for these fixed markers
4. Update tree probabilities based on fixed marker measurements

**Advantages**:
- Consistent clinical workflow
- Easier to standardize and validate
- Simpler for clinical implementation

**Use Case**: Clinical monitoring, patient management, treatment response assessment

---

## System Architecture

### Pipeline Overview

```
                    HPC Longitudinal Analysis Pipeline
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  Input Data                Analysis Modes              Output Generation    │
│  ┌─────────────┐           ┌─────────────────┐         ┌─────────────────┐  │
│  │ Tree        │──────────▶│ Dynamic Marker  │────────▶│ Figures (PNG)   │  │
│  │ Distributions│           │ Selection       │         │ Metrics (JSON)  │  │
│  │             │           └─────────────────┘         │ Comparison      │  │
│  │ Marker Data │           ┌─────────────────┐         │ Analysis        │  │
│  │             │──────────▶│ Fixed Marker    │────────▶│                 │  │
│  │ Patient     │           │ Tracking        │         │                 │  │
│  │ Metadata    │           └─────────────────┘         └─────────────────┘  │
│  └─────────────┘                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Input Processing**:
   - Load initial tree distributions from bootstrap analysis
   - Parse marker data and patient metadata
   - Validate data consistency and completeness

2. **Analysis Execution**:
   - **Dynamic Mode**: Iterative marker selection and tree updates
   - **Fixed Mode**: Initial marker selection followed by consistent tracking
   - Bayesian inference for tree probability updates in both modes

3. **Output Generation**:
   - Generate standardized figures for both approaches
   - Export structured metrics and performance comparisons
   - Create comprehensive analysis summary

### Output Structure

```
analysis_output/
├── figures/
│   ├── dynamic_analysis/
│   │   ├── tree_convergence_dynamic.png
│   │   ├── marker_selection_timeline.png
│   │   ├── vaf_timeseries_dynamic.png
│   │   └── objective_evolution.png
│   ├── fixed_analysis/
│   │   ├── tree_convergence_fixed.png
│   │   ├── fixed_marker_trajectories.png
│   │   ├── vaf_timeseries_fixed.png
│   │   └── measurement_confidence.png
│   └── comparative_analysis/
│       ├── approach_comparison.png
│       ├── convergence_comparison.png
│       └── performance_metrics.png
├── metrics/
│   ├── dynamic_results.json
│   ├── fixed_results.json
│   ├── comparative_analysis.json
│   └── analysis_summary.json
├── data/
│   ├── tree_distributions/        # Updated pickle files
│   └── marker_selections/         # Detailed selection data
└── logs/
    ├── analysis.log
    └── performance.log
```

### Key Data Structures

Understanding the existing data formats is crucial for development. The HPC pipeline works with these specific structures:

#### Tree Distribution Pickle Files
These are the core data files containing tree topology and frequency information:

```python
# Structure of *_bootstrap_summary_updated_*.pkl files
{
    'tree_structure': [...],      # List of tree topologies (adjacency matrices)
                                 # Each element represents one candidate tree
    'node_dict': [...],          # List of mutation assignments to nodes
                                 # Maps tree nodes to specific mutations (e.g., 's123')
    'node_dict_name': [...],     # List of gene names for mutations
                                 # Maps mutations to gene names (e.g., 'TP53', 'KRAS')
    'freq': [...],               # Tree frequencies/weights (probabilities)
                                 # Shows relative likelihood of each tree
    'vaf_frac': [...],          # VAF fractions for each node in each tree
                                 # Expected VAF values for mutations
    'clonal_freq': [...],       # Clonal frequencies for each node
                                 # Population frequencies of clones
    'timepoint': 'YYYY-MM-DD',   # Timepoint identifier
    'patient_id': 'CRUK0044'     # Patient identifier
}
```

#### Marker Selection JSON Files (Dynamic Approach)
Results from the dynamic marker selection optimization:

```python
# Structure of dynamic_marker_selection_*.json files
{
    'timepoint': '2023-01-15',
    'selected_markers': ['s123', 's456', 's789'],  # Selected mutation IDs
    'selected_gene_names': ['TP53', 'KRAS', 'PIK3CA'],  # Corresponding gene names
    'ddpcr_measurements': [0.12, 0.08, 0.15],      # Simulated ddPCR measurements
    'objective_fraction': 0.85,                     # Objective function value (fraction)
    'objective_structure': 0.92,                    # Objective function value (structure)
    'optimization_time': 45.2,                      # Time taken for optimization (seconds)
    'n_markers_selected': 3,                        # Number of markers selected
    'total_markers_available': 150,                 # Total markers available for selection
    'convergence_status': 'optimal'                 # Gurobi optimization status
}
```

#### Fixed Marker Tracking JSON Files (To Be Implemented)
Results from the fixed marker tracking approach:

```python
# Structure of fixed_marker_tracking_*.json files (NEW)
{
    'timepoint': '2023-01-15',
    'fixed_markers': ['s123', 's456', 's789'],     # Fixed marker set (same across timepoints)
    'marker_gene_names': ['TP53', 'KRAS', 'PIK3CA'], # Gene names for fixed markers
    'ddpcr_measurements': [0.12, 0.08, 0.15],      # ddPCR measurements for fixed markers
    'predicted_vaf': [0.11, 0.09, 0.14],          # Predicted VAF from tree ensemble
    'measurement_confidence': [0.95, 0.88, 0.92],  # Confidence in measurements
    'tree_update_applied': True,                    # Whether tree probabilities were updated
    'initial_selection_timepoint': '2023-01-01',   # When markers were initially selected
    'selection_criteria': 'max_information_gain'    # Criteria used for initial selection
}
```

#### Analysis Summary Metadata
Comprehensive metadata for the entire analysis:

```python
# Structure of analysis_summary.json
{
    'analysis_metadata': {
        'patient_id': 'CRUK0044',
        'analysis_date': '2024-01-15T10:30:00Z',
        'pipeline_version': '1.2.0',
        'timepoints': ['2023-01-01', '2023-02-01', '2023-03-01'],
        'n_timepoints': 3,
        'approaches_used': ['dynamic', 'fixed'],
        'convergence_achieved': True,
        'dominant_tree_id': 42
    },
    'tree_analysis': {
        'n_candidate_trees': 100,
        'n_mutations_total': 250,
        'tree_convergence_timepoint': 3,
        'final_tree_entropy': 0.15,
        'dominant_tree_frequency': 0.89
    },
    'marker_analysis': {
        'dynamic_approach': {
            'markers_per_timepoint': [5, 4, 3],
            'total_unique_markers': 8,
            'final_objective_fraction': 0.89,
            'final_objective_structure': 0.94,
            'optimization_time_total': 120.5
        },
        'fixed_approach': {
            'n_fixed_markers': 5,
            'fixed_markers': ['s123', 's456', 's789', 's012', 's345'],
            'marker_gene_names': ['TP53', 'KRAS', 'PIK3CA', 'APC', 'BRAF'],
            'final_objective_fraction': 0.82,
            'final_objective_structure': 0.88,
            'measurement_success_rate': 0.95
        }
    },
    'performance_comparison': {
        'convergence_speed': {
            'dynamic_timepoints': 3,
            'fixed_timepoints': 4
        },
        'final_accuracy': {
            'dynamic_score': 0.91,
            'fixed_score': 0.85
        },
        'clinical_practicality': {
            'dynamic_complexity': 'high',
            'fixed_complexity': 'low'
        }
    }
}
```

#### Data Loading Requirements

The system must handle these specific data characteristics:

- **File Naming Convention**: `{patient_id}_bootstrap_summary_updated_{timepoint}.pkl`
- **Pickle Protocol**: Python pickle protocol 4 or 5
- **Data Types**: Mixed numpy arrays, Python lists, and dictionaries
- **Size Range**: 10MB - 100MB per pickle file
- **Encoding**: UTF-8 for string data
- **Missing Data**: Handle gracefully when timepoints are missing
- **Version Compatibility**: Support data from different pipeline versions

---

## Implementation Strategy

### Core Objectives

1. **Implement Fixed Marker Functionality**: Add the missing fixed marker selection and tracking logic
2. **Create Figure Generation System**: Automated production of publication-ready figures
3. **Develop Metrics Export**: Structured JSON output for quantitative analysis
4. **Enable Comparative Analysis**: Direct comparison between dynamic and fixed approaches
5. **Ensure Robust Operation**: Handle edge cases and provide comprehensive logging

### Development Approach

**Priority 1: Core Functionality**
- Implement fixed marker selection algorithm
- Add fixed marker tracking across timepoints
- Ensure both modes produce comparable outputs

**Priority 2: Output Generation**
- Create comprehensive figure generation system
- Implement structured metrics export
- Add comparative analysis capabilities

**Priority 3: Robustness & Validation**
- Add comprehensive error handling
- Implement validation against known results
- Create performance benchmarking

---

## Development Tickets

### ~~Ticket 1: Fixed Marker Implementation~~ ✅ **COMPLETED**
**Priority**: ~~High~~ **COMPLETED** | **Estimated Time**: ~~5-6 days~~ **COMPLETED**

**Status**: ✅ **COMPLETED** - Fixed marker functionality has been fully implemented in `longitudinal_update.py`

**Completed Deliverables**:
- ✅ Fixed marker selection algorithm integrated into existing pipeline
- ✅ User-specified marker input via `--fixed-markers` parameter
- ✅ Tree probability update logic for fixed markers
- ✅ Validation against dynamic approach results
- ✅ Error handling for edge cases (missing markers, validation failures)
- ✅ Performance metrics collection and comparative analysis
- ✅ Production SLURM script (`longitudinal_analysis_fixed.sh`)

**Key Functions Implemented**:
```python
def validate_fixed_markers(fixed_markers, available_markers):
    """Validate user-specified markers against dataset."""
    
def process_fixed_marker_timepoint(tree_data, fixed_markers, timepoint_data):
    """Process single timepoint with fixed marker set."""
    
def run_fixed_marker_analysis(args):
    """Execute complete fixed marker workflow."""
    
def generate_comparative_analysis(dynamic_results, fixed_results):
    """Compare performance between approaches."""
```

**Clinical Integration Achieved**:
- ✅ Clinician-specified markers (e.g., `DLG2_11_83544685_T>A GPR65_14_88477948_G>T`)
- ✅ Consistent tracking across all timepoints
- ✅ Graceful handling of missing markers with validation feedback
- ✅ Structured output compatible with existing pipeline

---

### ~~Ticket 1.5: YAML Configuration and Technical Stability~~ ✅ **COMPLETED**
**Priority**: ~~Critical~~ **COMPLETED** | **Estimated Time**: ~~3-4 days~~ **COMPLETED**

**Status**: ✅ **COMPLETED** - Complete YAML configuration system implemented with technical fixes

**Completed Deliverables**:
- ✅ **YAML Configuration System**:
  - ✅ Complete migration from command-line arguments to structured YAML files
  - ✅ Robust configuration loading and validation with `load_config()` and `config_to_args()`
  - ✅ Production configuration templates for different analysis scenarios
  - ✅ Backward compatibility maintained with legacy command-line interface
- ✅ **Shell Parsing Resolution**:
  - ✅ Fixed truncation of mutation names containing `>` characters
  - ✅ Eliminated complex command-line escaping requirements
  - ✅ Improved script reliability and maintainability
- ✅ **Marker Validation System Fixes**:
  - ✅ Corrected critical `gene2idx` mapping bug preventing marker identification
  - ✅ Enhanced validation logic with detailed success/failure reporting
  - ✅ Graceful handling of missing markers with clear feedback
- ✅ **Numerical Stability Improvements**:
  - ✅ Implemented log-space arithmetic for large read depths (60,000+)
  - ✅ Added overflow protection using `scipy.special.gammaln`
  - ✅ Enhanced integration robustness with multiple fallback strategies
- ✅ **Enhanced Error Handling**:
  - ✅ Fixed UnboundLocalError in exception handling
  - ✅ Early logger initialization for robust error reporting
  - ✅ Comprehensive configuration validation with meaningful error messages

**Key Functions Implemented**:
```python
def load_config(config_file):
    """Load and validate YAML configuration with robust error handling."""

def config_to_args(config, cmd_args):
    """Convert YAML configuration to args namespace for compatibility."""

def validate_fixed_markers(fixed_markers, gene_name_list, gene2idx):
    """Enhanced marker validation with proper gene mapping."""

def integrand_single(f, d1, d2, r1, r2):
    """Compute integrand using log-space arithmetic to avoid overflow."""
```

**Production Integration Achieved**:
- ✅ YAML-compatible SLURM script (`longitudinal_yaml_analysis.sh`)
- ✅ Configuration templates for clinical and research workflows
- ✅ Validated with real patient data (CRUK0044) and large read depths
- ✅ Both dynamic and fixed marker approaches benefit from improvements

---

### Ticket 2: Enhanced Figure Generation System  
**Priority**: High | **Estimated Time**: 4-5 days

**Description**: Create a comprehensive figure generation system that produces publication-ready plots for both analysis approaches, with enhanced time series visualization.

**Requirements**:
- Generate all key figures for dynamic and fixed approaches
- **NEW**: Create time series plots showing clonal evolution over time
- Create comparative analysis plots
- Use consistent, publication-ready styling
- Support multiple output formats (PNG, PDF)
- Include proper legends, labels, and annotations
- Generate figure metadata and descriptions

**Key Figures to Generate**:

1. **Dynamic Analysis Figures**:
   - Tree convergence plot showing probability evolution
   - Marker selection timeline with objective function values
   - VAF time series for dynamically selected markers
   - Objective function evolution over timepoints

2. **Fixed Analysis Figures**:
   - Tree convergence plot for fixed marker approach
   - Fixed marker VAF trajectories over time
   - Measurement confidence visualization
   - Marker performance assessment

3. **Comparative Analysis Figures**:
   - Side-by-side convergence comparison
   - Performance metrics comparison
   - Statistical significance analysis
   - Clinical practicality assessment

4. **NEW: Time Series Visualization**:
   - Clonal fraction evolution over time
   - Individual marker VAF trajectories
   - Tree probability evolution
   - Temporal trends in overall clonal burden

**Updated Key Functions to Implement**:
```python
def generate_time_series_plots(longitudinal_data, approach='dynamic'):
    """Generate comprehensive time series visualizations."""
    
def generate_clonal_evolution_plot(tree_timeline, timepoints):
    """Generate clonal fraction evolution over time."""
    
def generate_marker_trajectory_plot(marker_data, approach='dynamic'):
    """Generate marker VAF trajectories over time."""
    
def generate_tree_probability_evolution(tree_data, timepoints):
    """Generate tree probability evolution visualization."""
    
def generate_comparative_time_series(dynamic_data, fixed_data):
    """Generate comparative time series analysis."""
```

---

### Ticket 3: Structured Metrics Export
**Priority**: Medium | **Estimated Time**: 3-4 days

**Description**: Implement comprehensive structured metrics export to JSON files for quantitative analysis and downstream processing.

**Requirements**:
- Export detailed metrics for both approaches
- Create comparative analysis metrics
- Include performance benchmarks and statistics
- Ensure machine-readable format with proper schema
- Add data validation and integrity checks
- Generate comprehensive analysis summary

**Updated Metrics to Export**:

1. **Dynamic Approach Metrics**:
   - Marker selection statistics by timepoint
   - Objective function evolution
   - Optimization performance metrics
   - Tree convergence analysis

2. **Fixed Approach Metrics**:
   - Fixed marker performance over time
   - Measurement confidence statistics
   - Tree probability evolution
   - Clinical practicality metrics

3. **Comparative Metrics**:
   - Convergence speed comparison
   - Final accuracy comparison
   - Statistical significance tests
   - Clinical workflow comparison

4. **NEW: Time Series Metrics**:
   - Clonal evolution rates
   - Marker stability metrics
   - Temporal correlation analysis
   - Prediction accuracy over time

---

### Ticket 4: Pipeline Integration & Testing
**Priority**: Medium | **Estimated Time**: 2-3 days

**Description**: Integrate enhanced visualization and metrics with existing pipeline and create comprehensive testing framework.

**Requirements**:
- Integrate figure generation and metrics export with existing pipeline workflow
- Add enhanced visualization to both SLURM scripts
- Create end-to-end testing with real data
- Add performance benchmarking
- Implement comprehensive error handling and logging
- Create pipeline configuration management

**Updated Deliverables**:
- Enhanced pipeline with comprehensive visualization
- Updated SLURM scripts with figure generation
- Comprehensive test suite
- Performance benchmarks
- Configuration management system
- Documentation and usage examples

---

## Updated Technical Specifications

### Current Implementation Status
- ✅ **Core Pipeline**: Both dynamic and fixed marker approaches operational
- ✅ **Command Line Interface**: Comprehensive argument parsing and validation
- ✅ **SLURM Integration**: Production scripts for both analysis modes
- ✅ **Clinical Workflow**: User-specified markers and validation
- ✅ **Comparative Analysis**: Built-in performance comparison
- ✅ **YAML Configuration**: Complete configuration management system
- ✅ **Technical Stability**: Marker validation and numerical overflow fixes
- ⏳ **Enhanced Visualization**: Time series plots and publication figures needed
- ⏳ **Structured Output**: Comprehensive JSON metrics needed

### Technology Stack
- **Core**: Python 3.8+
- **Data Processing**: pandas, numpy, pickle
- **Optimization**: Gurobi (for marker selection)
- **Visualization**: matplotlib, seaborn
- **Statistics**: scipy, statsmodels
- **Testing**: pytest, unittest
- **Logging**: Python logging module

### Performance Requirements
- **Processing Time**: <15 minutes for typical datasets (3-5 timepoints)
- **Memory Usage**: <6GB for large datasets (10+ timepoints)
- **Figure Generation**: <60 seconds for complete figure set
- **Output Size**: <1GB for complete analysis output
- **Scalability**: Handle up to 20 timepoints, 1000 candidate trees

---

## Updated Timeline Estimate

**Total Estimated Time**: 6-9 days (reduced from 15-19 days)

- ~~**Ticket 1** (Fixed Marker Implementation): 5-6 days~~ ✅ **COMPLETED**
- ~~**Ticket 1.5** (YAML Configuration & Technical Stability): 3-4 days~~ ✅ **COMPLETED**
- **Ticket 2** (Enhanced Figure Generation System): 4-5 days  
- **Ticket 3** (Structured Metrics Export): 3-4 days
- **Ticket 4** (Pipeline Integration & Testing): 2-3 days

**Critical Path**: Ticket 2 → Ticket 3 → Ticket 4

**Major Progress Achieved**: 
- ✅ **8-10 days of development completed** (Tickets 1 & 1.5)
- ✅ **Core functionality fully operational** with both analysis modes
- ✅ **Technical stability achieved** with robust error handling
- ✅ **Production deployment ready** with YAML configuration support

**Remaining Focus**: Enhanced visualization and structured output generation for comprehensive analysis reporting.

**Recommended Team**: 1-2 junior engineers with senior oversight

---

## Success Criteria

### Functional Requirements
- ✅ Fixed marker functionality implemented and validated
- ✅ Both analysis modes produce meaningful, comparable results
- ✅ YAML configuration system provides robust parameter management
- ✅ Technical issues resolved (marker validation, numerical stability)
- [ ] All key figures generated automatically with publication quality
- [ ] Comprehensive structured metrics exported to JSON
- [ ] Comparative analysis provides scientific insights
- [ ] Time series visualization shows temporal evolution clearly

### Quality Requirements
- ✅ Pipeline handles real patient data without errors
- ✅ Performance meets specified benchmarks
- ✅ Scientific results are validated against known outcomes
- ✅ Configuration system is robust and user-friendly
- ✅ Marker validation system works reliably
- ✅ Numerical computations are stable for large datasets
- [ ] Code follows best practices and is well-documented
- [ ] Error handling covers all major failure modes
- [ ] Enhanced visualizations are publication-ready

### Scientific Requirements
- ✅ Fixed marker approach produces clinically relevant results
- ✅ Comparison between approaches is statistically sound and interpretable
- ✅ Results are reproducible across multiple runs
- ✅ Configuration system enables consistent analysis workflows
- ✅ Marker validation ensures biological accuracy
- ✅ Numerical stability maintains computational integrity
- [ ] Figures clearly communicate key scientific findings
- [ ] Metrics enable quantitative downstream analysis
- [ ] Time series analysis reveals temporal patterns

---

## Getting Started

### Prerequisites
1. ✅ Python 3.8+ environment with existing dependencies
2. ✅ Access to current `5-long/longitudinal_update.py` implementation
3. ✅ Gurobi license and optimization environment
4. ✅ Sample patient data (CRUK0044) for testing and validation
5. ✅ Understanding of tumor evolution analysis and phylogenetic concepts

### Development Workflow
1. ~~**Start with Ticket 1**: Implement fixed marker functionality first~~ ✅ **COMPLETED**
2. ~~**Validate scientifically**: Ensure results make biological sense~~ ✅ **COMPLETED**
3. **Add enhanced figure generation**: Create comprehensive visual outputs including time series
4. **Export structured metrics**: Enable quantitative analysis
5. **Test comprehensively**: Validate with real patient data

### Current State Summary
The longitudinal analysis pipeline now has complete dual-mode functionality with both dynamic and fixed marker approaches operational. The remaining work focuses on enhanced visualization and structured output generation to provide comprehensive analysis results suitable for both research and clinical applications.

This pipeline will provide a solid foundation for tumor evolution analysis, supporting both research (dynamic) and clinical (fixed) workflows with comprehensive outputs for downstream analysis and publication. 