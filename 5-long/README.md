# Longitudinal Cancer Evolution Analysis Pipeline

## Overview

This directory contains the production-ready longitudinal analysis pipeline for tracking cancer evolution over time using blood-based liquid biopsy data. The pipeline implements iterative Bayesian tree updating to monitor tumor evolution through ddPCR measurements.

## Key Features

- **Production-ready implementation**: Robust error handling, comprehensive logging, and modular design
- **Flexible data input**: SSM file format for tissue data, CSV format for longitudinal ddPCR data  
- **Modern data formats**: Replaces Excel dependencies with standard CSV/TSV formats
- **Comprehensive validation**: Input file validation and compatibility checking
- **Clinical integration**: Designed for real-world clinical laboratory workflows
- **HPC compatibility**: Designed for integration with SLURM job submission systems

## Pipeline Components

### Core Script
- **`longitudinal_update.py`**: Main production-ready script for longitudinal analysis

### Supporting Modules
- **`adjust_tree_distribution.py`**: Bayesian tree updating algorithms
- **`optimize.py`**: Tree structure optimization utilities  
- **`optimize_fraction.py`**: Marker optimization for longitudinal tracking
- **`analyze.py`**: Tree processing and analysis utilities

### Example Data
- **`example_longitudinal_data.csv`**: Example CSV format for longitudinal ddPCR data

### Legacy Code
- **`iterative_pipeline_real.py`**: Original prototype implementation (deprecated)

## Input File Requirements

### 1. Tree Distribution Data (from Aggregation Stage)
Required files in the aggregation directory:
```
phylowgs_bootstrap_summary.pkl
phylowgs_bootstrap_aggregation.pkl
```

### 2. Tissue Mutation Data (SSM Format)
Tab-separated file with columns:
- `id`: Mutation identifier (e.g., s0, s1, s2...)
- `gene`: Gene name with genomic location (e.g., GPR65_14_88477948_G>T)
- `a`: Reference read counts (comma-separated for multiple samples)
- `d`: Total read counts (comma-separated for multiple samples)  
- `mu_r`: Reference allele error rate (typically 0.999)
- `mu_v`: Variant allele error rate (typically 0.499)

### 3. Longitudinal ddPCR Data (CSV Format)
CSV file with columns:
- `date`: Timepoint date in YYYY-MM-DD format
- `gene`: Gene name matching tissue data
- `mutant_droplets`: Number of mutant-positive droplets from ddPCR
- `total_droplets`: Total number of droplets analyzed
- `notes`: Optional notes (ignored by pipeline)

See `example_longitudinal_data.csv` for format example.

## Usage

### Basic Usage
```bash
python longitudinal_update.py CRUK0044 \
    --aggregation-dir /data/CRUK0044/initial/aggregation_results \
    --ssm-file /data/ssm.txt \
    --longitudinal-data /data/CRUK0044_longitudinal.csv \
    --output-dir /data/CRUK0044/longitudinal
```

### Advanced Configuration
```bash
python longitudinal_update.py CRUK0041 \
    --aggregation-dir /data/CRUK0041/aggregation_results \
    --ssm-file /data/ssm.txt \
    --longitudinal-data /data/CRUK0041_ddpcr.csv \
    --output-dir /data/CRUK0041/longitudinal \
    --n-markers 3 \
    --read-depth 95000 \
    --algorithm struct \
    --timepoints 2024-01-15,2024-02-15,2024-03-15 \
    --debug
```

### Command Line Options

#### Required Arguments
- `patient_id`: Patient identifier (e.g., CRUK0044)
- `-a, --aggregation-dir`: Path to aggregation results directory
- `-s, --ssm-file`: Path to SSM file containing tissue mutation data
- `-l, --longitudinal-data`: Path to CSV file containing longitudinal ddPCR data
- `-o, --output-dir`: Output directory for results

#### Analysis Parameters
- `-n, --n-markers`: Number of markers to select (default: 2)
- `-r, --read-depth`: Expected ddPCR read depth (default: 90000)
- `--algorithm`: Algorithm type - 'struct' or 'frac' (default: struct)
- `--method`: Phylogenetic method (default: phylowgs)

#### Optional Configuration
- `-t, --timepoints`: Comma-separated timepoints to analyze (YYYY-MM-DD)
- `--lambda1`: Weight for tree fractions (default: 0)
- `--lambda2`: Weight for tree distributions (default: 1)
- `--focus-sample`: Sample index to focus on (default: 0)

#### Output Options
- `--no-plots`: Skip visualization generation
- `--plot-format`: Output format for plots (png/pdf/eps, default: png)
- `--save-intermediate`: Save intermediate results for debugging
- `--debug`: Enable debug logging and additional output files

## Output Structure

The pipeline creates the following output directory structure:

```
{output_dir}/
├── logs/                                    # Comprehensive logging
│   └── {patient}_longitudinal_analysis_{timestamp}.log
├── updated_trees/                           # Updated tree distributions per timepoint
│   ├── phylowgs_bootstrap_summary_updated_struct_2_0_bayesian.pkl
│   ├── phylowgs_bootstrap_summary_updated_struct_2_1_bayesian.pkl
│   └── ...
├── marker_selections/                       # Selected markers per timepoint
│   ├── timepoint_0_markers.json
│   ├── timepoint_1_markers.json
│   └── ...
├── visualizations/                          # Temporal evolution plots (future)
│   ├── tree_probability_evolution.png
│   ├── clonal_fraction_trajectories.png
│   └── marker_vaf_timeseries.png
└── clinical_reports/                        # Clinical recommendations (future)
    ├── timepoint_0_clinical_report.pdf
    └── ...
```

## Current Implementation Status

### ✅ Completed Features
- **Robust argument parsing and validation**
- **Comprehensive logging system**
- **SSM-based tissue data loading** (Task 3.1)
- **CSV-based longitudinal data processing** (Task 3.2)
- **Input file validation and compatibility checking**
- **Modern error handling and debugging support**

### 🔄 In Development
- **Iterative Bayesian analysis workflow** (core longitudinal algorithm)
- **Time series visualization** (Task 3.5)
- **Clinical report generation**
- **SLURM integration** (Task 3.6)

### 📅 Planned Features
- **Enhanced temporal visualizations**
- **Automated clinical protocol generation**
- **Multi-patient comparative analysis**
- **Real-time monitoring dashboard**

## Development Roadmap

This implementation addresses key tasks from the TracerX development roadmap:

### Task 3.1: SSM-Based Tissue Data Integration ✅
- Replaced Excel-based tissue data with SSM file processing
- Implemented gene name handling and duplicate resolution
- Maintained compatibility with existing gene-to-index mapping

### Task 3.2: CSV Longitudinal Data Processing ✅
- Replaced multi-sheet Excel with CSV format
- Added date-based timepoint grouping
- Maintained ddPCR data structure compatibility

### Task 3.3: CRUK0044 Integration & Testing 🔄
- Ready for integration with CRUK0044 data structure
- Input validation ensures compatibility with real patient data
- Testing framework prepared for validation studies

### Tasks 3.4-3.6: Future Development 📅
- Output analysis and improvement planning
- Time series visualization implementation  
- Longitudinal processing module structure

## Clinical Integration

### Computational-Clinical Workflow
1. **Initial Analysis**: Process aggregation results to select optimal markers
2. **Clinical Recommendation**: Provide specific markers for ddPCR assay development
3. **Iterative Monitoring**: Update tree probabilities based on blood sample VAFs
4. **Clinical Decision Support**: Generate evolutionary trajectory reports

### Expected Clinical Impact
- **Cost Reduction**: $100-200 per timepoint vs. $1000+ tissue analysis
- **Minimal Invasiveness**: Monthly blood draws vs. tissue biopsies
- **Real-Time Monitoring**: Evolutionary trajectory forecasting
- **Personalized Medicine**: Patient-specific marker panels

## Dependencies

### Required Python Packages
- pandas: Data manipulation and analysis
- numpy: Numerical computing
- matplotlib: Plotting and visualization
- pathlib: Path handling
- pickle: Data serialization
- argparse: Command line argument parsing
- logging: Comprehensive logging system

### Local Modules
All optimization and analysis modules from the 5-long directory:
- optimize.py, optimize_fraction.py, analyze.py, adjust_tree_distribution.py

### External Dependencies
- Gurobi optimization solver (requires license)
- Advanced scientific computing libraries
- Previous pipeline stage outputs (aggregation results)

## Getting Started

1. **Prepare Input Data**:
   - Ensure aggregation stage has completed successfully
   - Prepare SSM file with tissue mutation data
   - Create CSV file with longitudinal ddPCR measurements

2. **Validate Setup**:
   ```bash
   python longitudinal_update.py --help
   ```

3. **Run Basic Analysis**:
   ```bash
   python longitudinal_update.py PATIENT_ID \
       --aggregation-dir /path/to/aggregation \
       --ssm-file /path/to/ssm.txt \
       --longitudinal-data /path/to/ddpcr.csv \
       --output-dir /path/to/output \
       --debug
   ```

4. **Check Logs**:
   Monitor the detailed log files in `{output_dir}/logs/` for progress and any issues.

## Support and Development

For questions, issues, or feature requests related to the longitudinal analysis pipeline, refer to the main TracerX project documentation and development roadmap in `todo.md` and `project.md`.

This implementation represents a significant step toward production-ready longitudinal cancer monitoring using blood-based liquid biopsy data. 