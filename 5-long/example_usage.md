# Longitudinal Analysis SLURM Script Usage

## Overview

The `longitudinal_analysis.sh` script runs the production-ready longitudinal cancer evolution analysis pipeline on HPC systems using SLURM job scheduling.

## Prerequisites

1. **Output directory must exist** - Create it before submitting the job
2. **Required input files**:
   - Aggregation results directory (from stage 4)
   - SSM file with tissue mutation data
   - Longitudinal CSV file with ddPCR data
3. **Environment**: Gurobi module and `markers_env` conda environment

## Basic Usage

```bash
# Create output directory first
mkdir -p /path/to/data/CRUK0044/longitudinal

# Submit SLURM job (code directory is now mandatory)
sbatch longitudinal_analysis.sh \
    CRUK0044 \
    /path/to/data/CRUK0044/initial/aggregation_results \
    /path/to/data/CRUK0044/ssm.txt \
    /path/to/data/cruk0044_liquid.csv \
    /path/to/data/CRUK0044/longitudinal \
    /path/to/tracerx-mp
```

## Advanced Usage with Custom Parameters

```bash
# Full parameter specification
sbatch longitudinal_analysis.sh \
    CRUK0044 \
    /path/to/data/CRUK0044/initial/aggregation_results \
    /path/to/data/CRUK0044/ssm.txt \
    /path/to/data/cruk0044_liquid.csv \
    /path/to/data/CRUK0044/longitudinal \
    /path/to/tracerx-mp \
    3 \
    95000 \
    struct \
    "--debug --save-intermediate"
```

## Parameters

| Position | Parameter | Default | Description |
|----------|-----------|---------|-------------|
| 1 | `patient_id` | Required | Patient identifier (e.g., CRUK0044) |
| 2 | `aggregation_directory` | Required | Path to aggregation results |
| 3 | `ssm_file_path` | Required | Path to SSM file |
| 4 | `longitudinal_data_csv` | Required | Path to longitudinal CSV |
| 5 | `output_directory` | Required | Output directory (must exist) |
| 6 | `code_directory` | Required | Path to TracerX repository base directory |
| 7 | `n_markers` | 2 | Number of markers to select |
| 8 | `read_depth` | 90000 | Expected ddPCR read depth |
| 9 | `algorithm` | struct | Algorithm type (struct/frac) |
| 10 | `additional_flags` | "" | Extra Python script flags |

## Additional Flags Examples

- `--debug`: Enable debug logging
- `--save-intermediate`: Save intermediate results
- `--no-plots`: Skip visualization generation
- `--timepoints 2014-11-28,2015-05-21`: Analyze specific timepoints only

## Output Structure

After successful completion, your output directory will contain:

```
/path/to/data/CRUK0044/longitudinal/
├── logs/
│   ├── longitudinal_analysis_execution.log
│   ├── longitudinal_analysis_execution.err
│   └── CRUK0044_longitudinal_analysis_YYYYMMDD_HHMMSS.log
├── updated_trees/
│   ├── phylowgs_bootstrap_summary_updated_struct_2_0_bayesian.pkl
│   └── phylowgs_bootstrap_summary_updated_struct_2_1_bayesian.pkl
└── marker_selections/
    ├── timepoint_0_markers.json
    └── timepoint_1_markers.json
```

## Job Monitoring

```bash
# Check job status
squeue -u $USER

# View live log output
tail -f /path/to/data/CRUK0044/longitudinal/logs/longitudinal_analysis_execution.log

# Check for errors
tail -f /path/to/data/CRUK0044/longitudinal/logs/longitudinal_analysis_execution.err
```

## Common Issues

1. **"Output directory not found"**: Create the output directory before submitting
2. **"Gurobi module failed"**: Ensure Gurobi license is available
3. **"markers_env not found"**: Activate the correct conda environment path
4. **"SSM file format error"**: Ensure SSM file has required columns (id, gene, a, d, mu_r, mu_v)
5. **"CSV format error"**: Ensure CSV has columns (gene, date, mutant_droplets, total_droplets)

## Example for CRUK0044

Assuming you have:
- Aggregation results in `/data/CRUK0044/initial/aggregation_results/`
- SSM file at `/data/CRUK0044/ssm.txt`
- Longitudinal CSV at `/data/cruk0044_liquid.csv`

```bash
# Create output directory
mkdir -p /data/CRUK0044/longitudinal

# Submit job with debug logging
sbatch 5-long/longitudinal_analysis.sh \
    CRUK0044 \
    /data/CRUK0044/initial/aggregation_results \
    /data/CRUK0044/ssm.txt \
    /data/cruk0044_liquid.csv \
    /data/CRUK0044/longitudinal \
    /path/to/tracerx-mp \
    2 \
    90000 \
    struct \
    "--debug"
``` 