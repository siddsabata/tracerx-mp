# TracerX Marker Selection Pipeline

## Project Overview
This project implements a computational pipeline for selecting genetic markers from cancer sequencing data. The pipeline processes somatic mutation data through several stages: bootstrapping, phylogenetic tree inference (PhyloWGS), aggregation of results, and marker selection. It is designed to analyze multi-region sequencing data from the TRACERx cohort to identify optimal genetic markers for tracking cancer evolution.

## Project Purpose and Roadmap

### Current Implementation (Initial Phase)
The currently implemented pipeline represents the **initial processing phase** of the TracerX marker selection project. This phase uses multi-region biopsy data to:
1. Construct phylogenetic trees representing cancer evolution
2. Identify optimal genetic markers for tracking cancer progression
3. Select markers suitable for monitoring via droplet digital PCR (ddPCR) blood samples

### Future Development (Longitudinal Phase)
The next phase of development (not yet implemented) will focus on **longitudinal analysis**:
1. Use blood sample data collected over time to update the tree distributions
2. Track clonal fractions over time to monitor cancer progression or treatment response
3. Converge to an optimal tree with the longitudinal update method
4. Provide temporal insights into cancer evolution during treatment

This dual-phase approach allows the pipeline to first establish a solid baseline understanding of the cancer's clonal structure from the initial biopsy, then refine this model over time with less-invasive blood samples.

## System Requirements
- High-Performance Computing (HPC) cluster with Slurm workload manager
- Conda package manager for environment management
- Python 3.x and required libraries (specified in environment.yml files)
- PhyloWGS software (installed via install_phylowgs.sh)

## Directory Structure
```
tracerx-mp/
├── main_init.sh              # Master orchestration script
├── install_phylowgs.sh       # PhyloWGS installation script
├── 1-bootstrap/             # Bootstrap stage
│   ├── bootstrap.sh         # Bootstrap job submission script
│   ├── bootstrap.py         # Bootstrap implementation
│   └── environment.yml      # Conda environment for bootstrap stage
├── 2-phylowgs/              # PhyloWGS stage
│   ├── phylowgs.sh          # PhyloWGS job submission script
│   └── environment.yml      # Conda environment for PhyloWGS
├── 3-aggregation/           # Aggregation stage
│   ├── aggregation.sh       # Aggregation job submission script
│   ├── aggregate.py         # Main aggregation implementation
│   ├── visualize.py         # Visualization utilities
│   ├── analyze.py           # Analysis utilities
│   ├── optimize.py          # Optimization utilities
│   └── environment.yml      # Conda environment for aggregation
├── 4-markers/               # Marker selection stage
│   ├── marker_selection.sh  # Marker selection job submission script
│   ├── run_data.py          # Data processing for marker selection
│   ├── run_markers.sh       # Marker selection execution script
│   ├── optimize_fraction.py # Fraction optimization implementation
│   ├── optimize.py          # General optimization utilities
│   └── environment.yml      # Conda environment for marker selection
└── data/                    # Input data directory containing sample SSM files
    ├── ssm.txt              # Sample somatic mutation data for patient CRUK0044
    └── ssm_subset.txt       # Subset with key mutations for testing 
```

## Input Data Format
The pipeline requires a Somatic Single Mutation (SSM) file as input, which contains the following columns:
- `id`: Unique mutation identifier (e.g., s0, s1, ...)
- `gene`: Gene name and genomic location (e.g., GPR65_14_88477948_G>T)
- `a`: Reference read depth across multiple tumor regions (comma-separated values)
- `d`: Total read depth across multiple tumor regions (comma-separated values)
- `mu_r`: Reference allele error rate (typically 0.999)
- `mu_v`: Variant allele error rate (typically 0.499)

Example from data/ssm.txt (TRACERx patient CRUK0044):
```
id  gene                      a               d               mu_r  mu_v
s0  GPR65_14_88477948_G>T     1287,1116,1262  2135,1233,1325  0.999 0.499
s1  GLIPR1L1_12_75728663_C>A  238,351,385     359,367,406     0.999 0.499
...
```

The comma-separated values in columns `a` and `d` represent data from multiple tumor regions of the same patient, which is the foundation for analyzing clonal evolution and selecting optimal genetic markers.

## Pipeline Components

### 1. Master Orchestration (`main_init.sh`)
- **Purpose**: Coordinates the entire pipeline execution
- **Inputs**:
  - Patient ID
  - Input SSM (Somatic Single Mutation) file
  - Patient base directory
  - Number of bootstraps (optional, default: 100)
  - Read depth (optional, default: 1500)
- **Outputs**:
  - Creates directory structure for pipeline execution
  - Submits jobs to Slurm scheduler
  - Generates log files in `{patient_base_dir}/initial/logs/`
- **Dependencies**: Slurm workload manager

### 2. Bootstrap Stage (`1-bootstrap/`)
- **Purpose**: Generates multiple bootstrap samples from input mutation data
- **Components**:
  - `bootstrap.sh`: Slurm job submission script
  - `bootstrap.py`: Python implementation of bootstrap sampling
- **Inputs**:
  - SSM file containing mutation data
  - Output directory
  - Number of bootstraps
- **Outputs**:
  - Multiple bootstrap samples in `{output_dir}/bootstraps/bootstrap1/, bootstrap2/, etc.`
  - Each bootstrap directory contains:
    - Input files for PhyloWGS
    - Execution logs in `{output_dir}/logs/`
- **Dependencies**: Python 3.x, conda environment `preprocess_env` (specified in `environment.yml`)

### 3. PhyloWGS Stage (`2-phylowgs/`)
- **Purpose**: Performs phylogenetic tree inference on bootstrap samples
- **Components**:
  - `phylowgs.sh`: Slurm job submission script
- **Inputs**:
  - Bootstrap samples directory (containing bootstrap1/, bootstrap2/, etc.)
- **Outputs**:
  - Phylogenetic trees for each bootstrap sample, stored inside each bootstrap directory:
    - `result.summ.json.gz`: Summary of phylogenetic trees
    - `result.muts.json.gz`: Mutation assignments
    - `result.mutass.zip`: Detailed mutation assignments
- **Dependencies**: PhyloWGS software, conda environment specified in `environment.yml`

### 4. Aggregation Stage (`3-aggregation/`)
- **Purpose**: Aggregates results from multiple bootstrap runs
- **Components**:
  - `aggregation.sh`: Slurm job submission script
  - `aggregate.py`: Main aggregation implementation
  - `visualize.py`: Visualization utilities
  - `analyze.py`: Analysis utilities
  - `optimize.py`: Optimization utilities
- **Inputs**:
  - Patient ID
  - Bootstrap samples directory (containing bootstrap1/, bootstrap2/, etc. with PhyloWGS results)
- **Outputs**:
  - Aggregated results in `{patient_base_dir}/initial/aggregation_results/`:
    - `{patient}_results_bootstrap_initial_best.json`: Best tree structure
    - `phylowgs_bootstrap_summary.pkl`: Summary of all trees
    - `phylowgs_bootstrap_aggregation.pkl`: Complete aggregation results
    - Various analysis plots and visualization files
- **Dependencies**: Python 3.x, conda environment `aggregation_env` (specified in `environment.yml`)

### 5. Marker Selection Stage (`4-markers/`)
- **Purpose**: Selects optimal genetic markers based on aggregated results
- **Components**:
  - `marker_selection.sh`: Slurm job submission script
  - `run_data.py`: Data processing implementation
  - `run_markers.sh`: Marker selection execution script
  - `optimize_fraction.py`: Fraction optimization implementation
  - `optimize.py`: General optimization utilities
- **Inputs**:
  - Patient ID
  - Aggregation results directory
  - Original SSM file
  - Read depth
- **Outputs**:
  - Selected markers in `{patient_base_dir}/initial/markers/`:
    - Marker lists
    - Optimization results
    - Performance metrics
- **Dependencies**: Python 3.x, conda environment `markers_env` (specified in `environment.yml`)

## Output Structure
For each patient, the pipeline creates the following directory structure:
```
{patient_base_dir}/
├── initial/
│   ├── bootstraps/          # Contains bootstrapN/ directories with PhyloWGS results
│   ├── aggregation_results/ # Contains aggregated tree structures and analyses
│   ├── markers/             # Contains final selected markers
│   └── logs/                # Pipeline execution logs
│       ├── pipeline_master.log
│       ├── slurm_*.out      # Slurm output logs
│       └── slurm_*.err      # Slurm error logs
```

## Running the Pipeline
1. Ensure all dependencies are installed:
   ```bash
   ./install_phylowgs.sh  # Install PhyloWGS
   ```

2. Run the pipeline:
   ```bash
   bash main_init.sh <patient_id> <input_ssm_file> <patient_base_dir> [num_bootstraps] [read_depth]
   ```
   Example:
   ```bash
   bash main_init.sh CRUK0044 data/ssm.txt /home/user/patient_data/CRUK0044/ 100 1500
   ```

3. Monitor progress:
   ```bash
   squeue -u $USER  # Check job status
   ```

## Environment Setup
Each stage has its own conda environment specified in `environment.yml`:
- Bootstrap: `preprocess_env`
- PhyloWGS: PhyloWGS-specific environment
- Aggregation: `aggregation_env`
- Marker Selection: `markers_env`

The environments are automatically activated by the respective shell scripts.

## Error Handling
- Each stage includes error checking and logging
- Failed jobs are reported in the respective error logs
- The pipeline uses Slurm's dependency system to ensure stages run in the correct order
- Detailed logs are maintained in the `logs` directory

## Notes for Developers
1. Each stage is modular and can be run independently if needed
2. All scripts include detailed logging for debugging
3. The pipeline uses absolute paths to ensure reliability
4. Environment files (`environment.yml`) should be updated if dependencies change
5. Future development will focus on implementing the longitudinal analysis phase 