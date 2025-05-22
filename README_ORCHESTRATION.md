# TracerX Pipeline Orchestration

This document explains how to use the new `main.sh` orchestration script for running the TracerX marker selection pipeline.

## Overview

The `main.sh` script is a robust orchestration system that:
- Submits all pipeline stages as Slurm jobs with proper dependencies
- Ensures sequential execution: bootstrap → phylowgs → aggregation → markers
- Handles dynamic array job sizing for PhyloWGS based on bootstrap count
- Provides comprehensive logging and error handling
- Creates a clean directory structure for all outputs

## Quick Start

### Basic Usage

```bash
# Make the script executable (first time only)
chmod +x main.sh

# Run the pipeline
./main.sh CRUK0044 data/ssm.txt /path/to/output

# With custom parameters
./main.sh CRUK0044 data/ssm.txt /path/to/output 50 2000
```

### Arguments

| Argument | Description | Default | Required |
|----------|-------------|---------|----------|
| `patient_id` | Patient identifier (e.g., CRUK0044) | - | Yes |
| `input_ssm_file` | Path to input SSM file | - | Yes |
| `output_base_dir` | Base directory for all outputs | - | Yes |
| `num_bootstraps` | Number of bootstrap samples | 100 | No |
| `read_depth` | Read depth for marker selection | 1500 | No |

## Directory Structure

The script creates the following directory structure:

```
output_base_dir/
└── initial/
    ├── bootstraps/           # Bootstrap samples (bootstrap1/, bootstrap2/, ...)
    ├── aggregation_results/  # Aggregated phylogenetic trees
    ├── markers/             # Final marker selection results
    └── logs/                # All pipeline logs
        ├── pipeline_master.log      # Main orchestration log
        ├── pipeline_config.txt      # Pipeline configuration
        ├── job_ids.txt             # Slurm job IDs
        ├── bootstrap_execution.log  # Bootstrap stage log
        ├── aggregation_execution.log # Aggregation stage log
        ├── marker_selection_execution.log # Marker selection log
        └── slurm_*.out/err         # Individual Slurm job logs
```

## Monitoring Pipeline Progress

### Using the Monitor Script

```bash
# Make monitor script executable
chmod +x monitor_pipeline.sh

# Check pipeline status
./monitor_pipeline.sh /path/to/output/initial/logs

# Continuous monitoring (updates every 30 seconds)
watch -n 30 ./monitor_pipeline.sh /path/to/output/initial/logs
```

### Manual Monitoring

```bash
# Check job status using job IDs
squeue -u $USER

# Check specific jobs (replace with actual job IDs)
squeue -j 12345,12346,12347,12348

# View master log
tail -f /path/to/output/initial/logs/pipeline_master.log

# Check for errors
find /path/to/output/initial/logs -name "*.err" -size +0
```

## Pipeline Stages

### 1. Bootstrap Stage
- **Purpose**: Generate bootstrap samples from input SSM data
- **Output**: `bootstraps/bootstrap1/`, `bootstrap2/`, etc.
- **Key files**: `ssm.txt`, `cnv.txt` in each bootstrap directory

### 2. PhyloWGS Stage
- **Purpose**: Infer phylogenetic trees for each bootstrap sample
- **Type**: Array job (parallel processing)
- **Output**: `result.summ.json.gz`, `result.muts.json.gz`, `result.mutass.zip` in each bootstrap directory

### 3. Aggregation Stage
- **Purpose**: Combine results from all bootstrap runs
- **Output**: `aggregation_results/` with tree distributions and analysis

### 4. Marker Selection Stage
- **Purpose**: Select optimal genetic markers based on aggregated results
- **Output**: `markers/` with final marker lists and optimization results

## Error Handling and Troubleshooting

### Common Issues

1. **Job Submission Failures**
   - Check Slurm configuration and permissions
   - Verify all required scripts exist
   - Check resource availability

2. **Path Issues**
   - The script automatically converts relative paths to absolute paths
   - Ensure input files exist before running

3. **Environment Issues**
   - Verify conda environments are properly set up
   - Check that PhyloWGS is installed (`./install_phylowgs.sh`)

### Debugging Steps

1. **Check the master log**:
   ```bash
   cat /path/to/output/initial/logs/pipeline_master.log
   ```

2. **Check individual stage logs**:
   ```bash
   # Bootstrap
   cat /path/to/output/initial/logs/bootstrap_execution.log
   
   # Aggregation
   cat /path/to/output/initial/logs/aggregation_execution.log
   
   # Marker selection
   cat /path/to/output/initial/logs/marker_selection_execution.log
   ```

3. **Check Slurm job logs**:
   ```bash
   # List all Slurm logs
   ls /path/to/output/initial/logs/slurm_*
   
   # Check specific job output
   cat /path/to/output/initial/logs/slurm_bootstrap_12345.out
   ```

4. **Check for errors**:
   ```bash
   find /path/to/output/initial/logs -name "*.err" -exec grep -l . {} \;
   ```

## Advanced Usage

### Custom PhyloWGS Array Configuration

The script automatically sets the PhyloWGS array size based on `num_bootstraps`. For 100 bootstraps, it creates an array job `0-99%10` (processing 100 samples with max 10 concurrent).

### Resource Customization

To modify resource requirements, edit the `#SBATCH` directives in individual stage scripts:
- `1-bootstrap/bootstrap.sh`
- `2-phylowgs/phylowgs.sh`
- `3-aggregation/aggregation.sh`
- `4-markers/marker_selection.sh`

### Running Individual Stages

While the orchestration script is recommended, you can run individual stages manually for debugging:

```bash
# Bootstrap only
sbatch 1-bootstrap/bootstrap.sh input.ssm output_dir code_dir 100

# PhyloWGS only (after bootstrap)
sbatch --array=0-99%10 2-phylowgs/phylowgs.sh bootstraps_dir code_dir

# Aggregation only (after PhyloWGS)
sbatch 3-aggregation/aggregation.sh patient_id bootstraps_dir code_dir

# Marker selection only (after aggregation)
sbatch 4-markers/marker_selection.sh patient_id aggregation_dir ssm_file code_dir read_depth
```

## Differences from Previous Version

The new `main.sh` script improves upon `main_init.sh` by:

1. **Simplified job submission**: Single function handles all job submissions
2. **Better error handling**: Comprehensive validation and error reporting
3. **Dynamic array sizing**: PhyloWGS array size adjusts to bootstrap count
4. **Improved logging**: Centralized logging with better organization
5. **Path handling**: Robust absolute path conversion
6. **Monitoring support**: Companion monitoring script for progress tracking
7. **Configuration saving**: Pipeline parameters saved for reference

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the pipeline logs for specific error messages
3. Ensure all dependencies are properly installed
4. Verify Slurm configuration and resource availability 