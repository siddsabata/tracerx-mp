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
- ⏳ **Fixed marker functionality missing**: Need to implement fixed marker selection and tracking
- ⏳ **Figure generation needed**: Automatic generation of key analysis plots
- ⏳ **Structured output needed**: Comprehensive JSON metrics and metadata
- ⏳ **Two-mode operation needed**: Pipeline should support both approaches seamlessly

### Target Deliverable
A complete HPC pipeline that:
1. **Processes both approaches**: Dynamic marker selection and fixed marker tracking
2. **Generates publication-ready figures**: PNG/PDF plots for all key analyses
3. **Outputs structured metrics**: JSON files with comprehensive analysis results
4. **Provides comparative analysis**: Performance comparison between approaches
5. **Runs autonomously**: Complete analysis from initial data to final outputs

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

### Ticket 1: Fixed Marker Implementation
**Priority**: High | **Estimated Time**: 5-6 days

**Description**: Implement the complete fixed marker selection and tracking functionality to complement the existing dynamic approach.

**Requirements**:
- Add fixed marker selection logic using initial timepoint optimization
- Implement consistent marker tracking across all timepoints  
- Create tree probability updates using only the fixed marker set
- Ensure output format consistency with dynamic approach
- Handle edge cases (marker dropout, measurement failures)

**Deliverables**:
- Fixed marker selection algorithm integrated into existing pipeline
- Tree probability update logic for fixed markers
- Validation against dynamic approach results
- Error handling for edge cases
- Performance metrics collection

**Key Functions to Implement**:
```python
def select_fixed_markers(initial_tree_data, n_markers=10):
    """Select optimal markers from initial timepoint analysis."""
    
def track_fixed_markers_across_timepoints(tree_timeline, fixed_markers):
    """Apply fixed marker tracking across all timepoints."""
    
def update_tree_probabilities_fixed(tree_data, marker_measurements):
    """Update tree probabilities using fixed marker measurements."""
    
def validate_fixed_marker_results(fixed_results, dynamic_results):
    """Validate fixed marker results against dynamic approach."""
```

**Acceptance Criteria**:
- [ ] Fixed markers selected optimally from initial timepoint
- [ ] Consistent tracking across all subsequent timepoints
- [ ] Tree probability updates work correctly
- [ ] Results are scientifically validated
- [ ] Performance is comparable to dynamic approach
- [ ] Edge cases handled gracefully

---

### Ticket 2: Figure Generation System  
**Priority**: High | **Estimated Time**: 4-5 days

**Description**: Create a comprehensive figure generation system that produces publication-ready plots for both analysis approaches.

**Requirements**:
- Generate all key figures for dynamic and fixed approaches
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

**Deliverables**:
- Complete figure generation pipeline
- Standardized plotting functions for each figure type
- Consistent styling and formatting
- Figure metadata export
- Example output figures with real data

**Key Functions to Implement**:
```python
def generate_tree_convergence_plot(tree_data, approach='dynamic'):
    """Generate tree frequency convergence visualization."""
    
def generate_marker_timeline_plot(marker_data, approach='dynamic'):
    """Generate marker selection/tracking timeline."""
    
def generate_vaf_timeseries_plot(vaf_data, approach='dynamic'):
    """Generate VAF trajectories over time."""
    
def generate_comparative_analysis_plots(dynamic_data, fixed_data):
    """Generate comparison plots between approaches."""
    
def apply_publication_styling():
    """Apply consistent publication-ready styling to all plots."""
```

**Acceptance Criteria**:
- [ ] All key figure types are implemented
- [ ] Figures are publication-ready quality
- [ ] Consistent styling across all plots
- [ ] Multiple output formats supported
- [ ] Figure metadata is comprehensive
- [ ] Performance is acceptable for large datasets

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

**Metrics to Export**:

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

**Deliverables**:
- Comprehensive JSON schema for all metrics
- Metrics calculation and export functions
- Data validation and quality checks
- Statistical analysis functions
- Example output files with documentation

**Key Functions to Implement**:
```python
def calculate_convergence_metrics(tree_timeline):
    """Calculate tree convergence statistics."""
    
def calculate_marker_performance_metrics(marker_data):
    """Calculate marker selection/tracking performance."""
    
def calculate_comparative_metrics(dynamic_results, fixed_results):
    """Calculate comparative performance metrics."""
    
def export_structured_metrics(all_metrics, output_dir):
    """Export all metrics to structured JSON files."""
    
def validate_metrics_schema(metrics_data):
    """Validate metrics against defined schema."""
```

**Acceptance Criteria**:
- [ ] All key metrics are calculated and exported
- [ ] JSON schema is well-defined and validated
- [ ] Comparative analysis is statistically sound
- [ ] Data integrity checks pass
- [ ] Output is machine-readable and documented

---

### Ticket 4: Pipeline Integration & Testing
**Priority**: Medium | **Estimated Time**: 3-4 days

**Description**: Integrate all components into a cohesive pipeline and create comprehensive testing framework.

**Requirements**:
- Integrate fixed marker functionality with existing pipeline
- Add figure generation and metrics export to pipeline workflow
- Create end-to-end testing with real data
- Add performance benchmarking
- Implement comprehensive error handling and logging
- Create pipeline configuration management

**Deliverables**:
- Integrated pipeline with both analysis modes
- Comprehensive test suite
- Performance benchmarks
- Configuration management system
- Documentation and usage examples

**Key Functions to Implement**:
```python
def run_longitudinal_analysis(config):
    """Main pipeline function supporting both analysis modes."""
    
def validate_pipeline_inputs(input_data):
    """Validate all input data before analysis."""
    
def run_comprehensive_tests():
    """Execute full test suite with validation."""
    
def benchmark_pipeline_performance():
    """Measure and report pipeline performance metrics."""
```

**Acceptance Criteria**:
- [ ] Pipeline runs both modes seamlessly
- [ ] All outputs are generated correctly
- [ ] Test suite covers major functionality
- [ ] Performance benchmarks are established
- [ ] Error handling is comprehensive
- [ ] Configuration is externalized and documented

---

## Technical Specifications

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

### Data Requirements
- **Input**: Tree distribution pickles, marker metadata
- **Timepoints**: Support 2-20 timepoints
- **Trees**: Handle 10-1000 candidate trees
- **Markers**: Process 10-2000 potential markers
- **Patients**: Single patient analysis per run

### Output Specifications
- **Figures**: High-resolution PNG (300 DPI) and vector PDF
- **Metrics**: Structured JSON with comprehensive metadata
- **Data**: Updated pickle files with analysis results
- **Logs**: Detailed analysis and error logs

---

## Testing Strategy

### Validation Approach

#### Scientific Validation
- **Known Results**: Test against validated datasets with expected outcomes
- **Mathematical Correctness**: Verify Bayesian inference and optimization algorithms
- **Statistical Significance**: Validate comparative analysis methods
- **Edge Cases**: Test with challenging data scenarios

#### Performance Testing
- **Scalability**: Test with varying dataset sizes
- **Memory Usage**: Monitor memory consumption patterns
- **Processing Speed**: Benchmark execution times
- **Output Quality**: Validate figure and metrics quality

#### Integration Testing
- **End-to-End**: Complete pipeline execution with real data
- **Mode Switching**: Seamless operation in both analysis modes
- **Output Validation**: Verify all outputs are generated correctly
- **Error Handling**: Test failure scenarios and recovery

### Test Data Requirements
- **Synthetic Data**: Generated datasets with known properties
- **Real Patient Data**: CRUK0044 and additional patient datasets
- **Edge Cases**: Datasets with missing timepoints, failed measurements
- **Large Scale**: High-complexity datasets for performance testing

### Success Metrics
- **Accuracy**: Results match expected scientific outcomes
- **Performance**: Meets specified timing and memory requirements
- **Robustness**: Handles edge cases without failure
- **Usability**: Clear outputs that support scientific interpretation

---

## Success Criteria

### Functional Requirements
- [ ] Fixed marker functionality implemented and validated
- [ ] Both analysis modes produce meaningful, comparable results
- [ ] All key figures generated automatically with publication quality
- [ ] Comprehensive structured metrics exported to JSON
- [ ] Comparative analysis provides scientific insights

### Quality Requirements
- [ ] Pipeline handles real patient data without errors
- [ ] Performance meets specified benchmarks
- [ ] Scientific results are validated against known outcomes
- [ ] Code follows best practices and is well-documented
- [ ] Error handling covers all major failure modes

### Scientific Requirements
- [ ] Fixed marker approach produces clinically relevant results
- [ ] Comparison between approaches is statistically sound and interpretable
- [ ] Results are reproducible across multiple runs
- [ ] Figures clearly communicate key scientific findings
- [ ] Metrics enable quantitative downstream analysis

---

## Timeline Estimate

**Total Estimated Time**: 15-19 days

- **Ticket 1** (Fixed Marker Implementation): 5-6 days
- **Ticket 2** (Figure Generation System): 4-5 days  
- **Ticket 3** (Structured Metrics Export): 3-4 days
- **Ticket 4** (Pipeline Integration & Testing): 3-4 days

**Critical Path**: Ticket 1 → Ticket 2 → Ticket 3 → Ticket 4

**Recommended Team**: 2-3 junior engineers with senior oversight

---

## Getting Started

### Prerequisites
1. Python 3.8+ environment with existing dependencies
2. Access to current `5-long/longitudinal_update.py` implementation
3. Gurobi license and optimization environment
4. Sample patient data (CRUK0044) for testing and validation
5. Understanding of tumor evolution analysis and phylogenetic concepts

### Development Workflow
1. **Start with Ticket 1**: Implement fixed marker functionality first
2. **Validate scientifically**: Ensure results make biological sense
3. **Add figure generation**: Create visual outputs for validation
4. **Export structured metrics**: Enable quantitative analysis
5. **Test comprehensively**: Validate with real patient data

### Key Success Factors
- **Scientific accuracy**: All implementations must be scientifically sound
- **Code clarity**: Simple, readable implementations over complex optimizations
- **Comprehensive testing**: Validate with multiple datasets and scenarios
- **Documentation**: Clear documentation of all methods and outputs
- **Stakeholder feedback**: Regular validation with domain experts

This pipeline will provide a solid foundation for tumor evolution analysis, supporting both research (dynamic) and clinical (fixed) workflows with comprehensive outputs for downstream analysis and publication. 