# TracerX Marker Selection Pipeline

## Overview

The TracerX Marker Selection Pipeline is a computational framework for identifying optimal genetic markers from cancer sequencing data. This pipeline processes somatic mutation data through several stages: bootstrapping, phylogenetic tree inference, aggregation of results, marker selection, and longitudinal tracking. It is designed to analyze multi-region sequencing data from the TRACERx cohort to identify optimal genetic markers for tracking cancer evolution over time.

## Quick Start

### Prerequisites
- High-Performance Computing (HPC) cluster with SLURM workload manager
- Conda package manager for environment management
- Python 3.x and required libraries
- PhyloWGS software (installed via setup script)

### Installation
```bash
# Install PhyloWGS dependencies
bash setup/install_phylowgs.sh

# Configure conda environments (see individual environment.yml files)
```

### Basic Usage

#### Single Patient Analysis
```bash
# Run complete pipeline (stages 1-4)
bash pipelines/master_pipeline.sh configs/templates/standard_analysis.yaml

# Test with minimal configuration
bash pipelines/master_pipeline.sh configs/templates/test_analysis.yaml --dry-run
```

#### Multi-Patient Analysis
```bash
# Process multiple patients
bash pipelines/multi_patient_pipeline.sh data/test_patients/ configs/templates/template_multi_patient.yaml /path/to/output/

# With delays between submissions
bash pipelines/multi_patient_pipeline.sh data/test_patients/ configs/templates/template_multi_patient.yaml /path/to/output/ --delay=60
```

#### Longitudinal Analysis
```bash
# Run longitudinal marker tracking
python src/longitudinal/longitudinal_main.py --config configs/examples/cruk0044_fixed.yaml
```

## Repository Structure

```
tracerx-mp/
├── README.md                    # This file
├── CLEANUP_PLAN.md             # Documentation of restructuring process
├── setup/                      # Installation and setup
│   ├── install_phylowgs.sh    # PhyloWGS installation script
│   └── environment_setup.md   # Setup documentation
├── src/                        # All source code organized by function
│   ├── bootstrap/              # Stage 1: Bootstrap sampling
│   ├── phylowgs/              # Stage 2: Phylogenetic inference
│   ├── aggregation/           # Stage 3: Result aggregation
│   ├── markers/               # Stage 4: Marker selection
│   ├── longitudinal/          # Stage 5: Longitudinal analysis
│   └── shared/                # Shared utilities
├── pipelines/                  # Main orchestration scripts
│   ├── master_pipeline.sh     # Single-patient pipeline orchestrator
│   └── multi_patient_pipeline.sh  # Multi-patient processing
├── configs/                    # Configuration files
│   ├── templates/             # Template configurations for different scenarios
│   └── examples/              # Example patient-specific configurations
├── data/                       # Sample and test data
│   ├── examples/              # Small example datasets
│   └── test_patients/         # Test patient data
├── batch_data/                 # Large batch datasets
│   └── ahn_june2023/          # Production batch data
└── docs/                       # All documentation
    ├── README_CONFIGURATION.md     # Configuration guide
    ├── README_MULTI_PATIENT.md     # Multi-patient usage
    ├── project_overview.md         # Detailed project overview
    └── [other documentation files]
```

## Pipeline Stages

### Stage 1: Bootstrap Sampling
Generates multiple bootstrap samples from input mutation data to quantify uncertainty.
- **Location**: `src/bootstrap/`
- **Entry Point**: `bootstrap.sh`
- **Output**: Multiple bootstrap samples for phylogenetic inference

### Stage 2: Phylogenetic Inference (PhyloWGS)
Performs phylogenetic tree inference on bootstrap samples using PhyloWGS.
- **Location**: `src/phylowgs/`
- **Entry Point**: `phylowgs.sh`
- **Output**: Phylogenetic trees for each bootstrap sample

### Stage 3: Result Aggregation
Aggregates results from multiple bootstrap runs and creates visualizations.
- **Location**: `src/aggregation/`
- **Entry Point**: `aggregation.sh`
- **Output**: Aggregated tree structures, best tree identification, visualizations

### Stage 4: Marker Selection
Selects optimal genetic markers based on aggregated results.
- **Location**: `src/markers/`
- **Entry Point**: `marker_selection.sh`
- **Output**: Selected markers with optimization results

### Stage 5: Longitudinal Analysis
Implements iterative Bayesian tree updating using blood sample data over time.
- **Location**: `src/longitudinal/`
- **Entry Point**: `longitudinal_main.py`
- **Output**: Updated tree distributions, temporal evolution analysis

## Key Features

- **YAML Configuration**: Unified configuration system replacing complex command-line arguments
- **Multi-Patient Support**: Batch processing capabilities for multiple patients
- **HPC Integration**: Native SLURM support with intelligent resource allocation
- **Flexible Analysis**: Support for both dynamic and fixed marker approaches
- **Comprehensive Visualization**: Publication-quality plots and analysis summaries
- **Robust Error Handling**: Extensive validation and meaningful error messages

## Configuration

The pipeline uses YAML configuration files for easy setup and reproducible analysis:

- **`configs/templates/standard_analysis.yaml`**: Production analysis
- **`configs/templates/test_analysis.yaml`**: Development and testing
- **`configs/templates/high_depth_analysis.yaml`**: Research-grade analysis
- **`configs/templates/template_multi_patient.yaml`**: Multi-patient processing

See `docs/README_CONFIGURATION.md` for detailed configuration options.

## Documentation

- **Project Overview**: `docs/project_overview.md` - Comprehensive project description
- **Configuration Guide**: `docs/README_CONFIGURATION.md` - YAML configuration details
- **Multi-Patient Guide**: `docs/README_MULTI_PATIENT.md` - Batch processing instructions
- **Implementation Details**: `docs/` - Additional technical documentation

## Input Data Format

The pipeline requires SSM (Somatic Single Mutation) files with the following format:

```
id  gene                      a               d               mu_r  mu_v
s0  GPR65_14_88477948_G>T     1287,1116,1262  2135,1233,1325  0.999 0.499
s1  GLIPR1L1_12_75728663_C>A  238,351,385     359,367,406     0.999 0.499
```

Where:
- `id`: Unique mutation identifier
- `gene`: Gene name with genomic coordinates
- `a`: Reference read depths (comma-separated for multiple samples)
- `d`: Total read depths (comma-separated for multiple samples)
- `mu_r`, `mu_v`: Error rates for reference and variant alleles

## Support and Development

This pipeline is designed for cancer genomics research with a focus on:
- **Reproducible Research**: Version-controlled configurations and analysis parameters
- **Clinical Translation**: Fixed marker approaches for clinical implementation
- **Scalable Processing**: Multi-patient and HPC-optimized workflows
- **Extensible Architecture**: Modular design for easy enhancement and customization

## Authors

TracerX Pipeline Development Team

## License

[Specify license information as appropriate]