# Environment Setup Guide

## Overview

The TracerX Pipeline uses multiple conda environments optimized for each stage of the analysis. This guide provides instructions for setting up these environments.

## Required Software

- **Conda/Miniconda**: Package and environment management
- **SLURM**: HPC job scheduling (for cluster deployment)
- **Git**: Version control (for PhyloWGS installation)
- **GCC**: C++ compiler (for PhyloWGS compilation)

## Installation Steps

### 1. Install PhyloWGS

```bash
# Run the PhyloWGS installation script
bash setup/install_phylowgs.sh
```

This script will:
- Clone the PhyloWGS repository to `src/phylowgs/phylowgs/`
- Compile the required C++ components
- Set up the PhyloWGS environment

### 2. Create Conda Environments

Each pipeline stage has its own environment specification:

#### Bootstrap Environment
```bash
conda env create -f src/bootstrap/environment.yml
```

#### PhyloWGS Environment
```bash
conda env create -f src/phylowgs/environment.yml
```

#### Aggregation Environment
```bash
conda env create -f src/aggregation/environment.yml
```

#### Markers Environment
```bash
conda env create -f src/markers/environment.yml
```

#### Longitudinal Environment
```bash
conda env create -f src/longitudinal/environment.yml
```

### 3. Verify Installation

Test the installation by running a dry-run:

```bash
# Test basic pipeline configuration
bash pipelines/master_pipeline.sh configs/templates/test_analysis.yaml --dry-run

# Check PhyloWGS installation
conda activate phylowgs_env
python2 src/phylowgs/phylowgs/multievolve.py --help
```

## Environment Details

### Environment Naming Convention
- `preprocess_env`: Bootstrap and data preprocessing
- `phylowgs_env`: PhyloWGS phylogenetic inference
- `aggregation_env`: Result aggregation and visualization
- `markers_env`: Marker selection and optimization
- `longitudinal_env`: Longitudinal analysis and Bayesian updating

### Key Dependencies
- **Python 3.x**: Main analysis framework
- **Python 2.7**: Required for PhyloWGS (legacy)
- **NumPy/SciPy**: Numerical computing
- **Pandas**: Data manipulation
- **Matplotlib/Seaborn**: Visualization
- **Gurobi**: Optimization solver (requires license)
- **PyYAML**: Configuration file parsing

## Troubleshooting

### Common Issues

#### PhyloWGS Compilation Errors
```bash
# Install required development tools
sudo apt-get install build-essential
sudo apt-get install libgsl-dev

# Or on CentOS/RHEL
sudo yum groupinstall "Development Tools"
sudo yum install gsl-devel
```

#### Gurobi License Issues
1. Obtain academic license from Gurobi website
2. Follow installation instructions for your environment
3. Verify license activation: `gurobi_cl --license`

#### Environment Conflicts
```bash
# Clean and recreate environments if needed
conda env remove -n markers_env
conda env create -f src/markers/environment.yml
```

### SLURM Configuration

For HPC deployment, ensure your SLURM configuration supports:
- Job arrays for parallel processing
- Module loading (if using environment modules)
- Appropriate resource limits and partitions

Example SLURM module loading (if applicable):
```bash
module load conda
module load gurobi
```

## Performance Tuning

### Resource Allocation Guidelines

- **Bootstrap**: 2-4 CPUs, 8-16 GB memory
- **PhyloWGS**: 4-8 CPUs, 8-16 GB memory per job
- **Aggregation**: 1-2 CPUs, 16-32 GB memory
- **Markers**: 1-2 CPUs, 16-32 GB memory, Gurobi license
- **Longitudinal**: 2-4 CPUs, 16-32 GB memory

### Cluster Optimization

For large-scale processing:
1. Use template configurations optimized for your cluster
2. Adjust array job limits based on cluster policies
3. Consider job submission delays for multi-patient processing
4. Monitor resource usage and adjust configurations accordingly

## Next Steps

After successful setup:
1. Test with the minimal configuration: `configs/templates/test_analysis.yaml`
2. Process example data: `data/examples/ssm_subset.txt`
3. Review output structure and logs
4. Proceed with your analysis data

For detailed usage instructions, see the main README.md and documentation in `docs/`.