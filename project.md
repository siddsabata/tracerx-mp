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

## Important Implementation Note
**Code and Data Directory Separation**: This pipeline is designed with a clear separation between:
1. **Code Directory**: Where the pipeline scripts and tools are stored (e.g., `/path/to/tracerx-mp/`)
2. **Data/Output Directories**: Where input data and analysis results are stored (e.g., `/path/to/patient_data/`)

When running pipeline components, absolute paths must be used to reference both code and data locations since Slurm job submission can change the working directory. All scripts should account for this separation to ensure proper operation on different systems.

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

### **Multi-Sample Data Processing**
The pipeline now includes robust multi-sample support through `convert_ssm_to_dataframe_v2.py`, which:
- **Automatically detects** the number of samples per mutation (2 to n samples)
- **Calculates VAFs** for each sample: VAF = (total_depth - ref_count) / total_depth
- **Applies flexible filtering** strategies to maintain data consistency with tree distributions
- **Validates compatibility** between filtered mutation sets and pre-computed phylogenetic trees

This ensures that the marker selection algorithms receive properly formatted data that matches the tree distribution expectations.

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
  - Code directory (absolute path to tracerx-mp directory)
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
  - `run_data.py`: Original data processing implementation (legacy)
  - `run_data_multi_sample.py`: **New multi-sample compatible implementation**
  - `convert_ssm_to_dataframe_v2.py`: **Multi-sample SSM to DataFrame converter**
  - `run_markers.sh`: Marker selection execution script
  - `optimize_fraction.py`: Fraction optimization implementation
  - `optimize.py`: General optimization utilities
- **Inputs**:
  - Patient ID
  - Aggregation results directory
  - Original SSM file
  - Read depth
  - **New**: VAF filtering strategy and parameters
- **Outputs**:
  - Selected markers in `{patient_base_dir}/initial/markers/`:
    - Marker lists
    - Optimization results
    - Performance metrics
    - **New**: Multi-sample filtering reports
- **Dependencies**: Python 3.x, conda environment `markers_env` (specified in `environment.yml`)

#### **Multi-Sample SSM Support**
The marker selection stage now supports variable numbers of samples (2 to n) with flexible VAF filtering strategies:
- **`any_high`**: Filter if ANY sample VAF ≥ threshold (most restrictive)
- **`all_high`**: Filter if ALL sample VAFs ≥ threshold (least restrictive)
- **`majority_high`**: Filter if >50% of sample VAFs ≥ threshold
- **`specific_samples`**: Filter based on specific sample indices

This resolves data consistency issues between SSM input and tree distribution data.

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

3. **Alternative: Run marker selection with multi-sample support directly:**
   ```bash
   cd 4-markers
   python run_data_multi_sample.py CRUK0044 \
     --ssm-file ../data/ssm.txt \
     --aggregation-dir /path/to/aggregation_results \
     --filter-strategy any_high \
     --filter-threshold 0.9 \
     --read-depth 1500
   ```

4. Monitor progress:
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
5. **Multi-sample support**: Use `run_data_multi_sample.py` for new analyses; `run_data.py` is maintained for legacy compatibility
6. **Data consistency**: The new multi-sample converter ensures filtered mutation sets match tree distribution expectations
7. Future development will focus on implementing the longitudinal analysis phase

### Path Resolution in SLURM Environment
#### Problem Identified
When running component scripts through Slurm, the working directory of the job is changed to a temporary directory (e.g., `/var/spool/slurmd/job123456/`), causing relative paths to break. This affects:
- Finding Python scripts from shell scripts
- Loading configuration files
- Writing output to the correct location

#### Solution Implemented
1. **Required Parameter Addition**: Component scripts now accept an explicit code directory parameter. For example:
   ```bash
   sbatch 1-bootstrap/bootstrap.sh <input_file> <output_dir> <code_dir> [other_params]
   ```

2. **Absolute Path Construction**: Inside each component script, absolute paths are constructed using the provided code directory:
   ```bash
   BOOTSTRAP_PY_PATH="${CODE_DIR}/1-bootstrap/bootstrap.py"
   ```

3. **Robust Path Verification**: Scripts now explicitly verify file existence before attempting execution.

#### Required Updates
To implement this fix across the pipeline:

1. **Component Scripts**: All stage scripts (phylowgs.sh, aggregation.sh, marker_selection.sh) need to be updated to:
   - Accept a code directory parameter
   - Use absolute paths to reference Python scripts and other dependencies
   - Add explicit file existence checks

2. **Main Orchestration Script**: The main_init.sh script needs to be updated to:
   - Pass its own directory as the code directory to all component scripts
   - Modify the submit_job function to handle the additional parameter

This ensures the pipeline works reliably regardless of Slurm's job directory behavior. 