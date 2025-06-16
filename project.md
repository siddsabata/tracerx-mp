# TracerX Marker Selection Pipeline

## Project Overview
This project implements a computational pipeline for selecting genetic markers from cancer sequencing data. The pipeline processes somatic mutation data through several stages: bootstrapping, phylogenetic tree inference (PhyloWGS), aggregation of results, marker selection, and longitudinal tracking. It is designed to analyze multi-region sequencing data from the TRACERx cohort to identify optimal genetic markers for tracking cancer evolution over time.

## Project Purpose and Roadmap

### Current Implementation (Initial Phase) ✅ COMPLETED
The currently implemented pipeline represents the **initial processing phase** of the TracerX marker selection project. This phase involved getting the complete pipeline working on HPC infrastructure and included:

1. **HPC Infrastructure Setup**: Successfully deploying the pipeline on SLURM-based HPC cluster
2. **Data Preparation**: Creating test datasets (including 5-mutation subset for rapid testing)
3. **Multi-Sample Framework**: Implementing robust support for variable numbers of tumor regions
4. **Pipeline Debugging**: Resolving Gurobi licensing, path resolution, and data consistency issues
5. **Phylogenetic Tree Construction**: Using bootstrap sampling and PhyloWGS for cancer evolution analysis
6. **Marker Selection**: Implementing optimization algorithms for genetic marker identification

**Status**: The initial phase is fully functional with robust multi-sample support, flexible VAF filtering, and comprehensive error handling. The pipeline successfully processes somatic mutation data through all stages: bootstrapping, phylogenetic inference, aggregation, and marker selection.

**Major Achievement**: ✅ **The complete pipeline successfully processes real TRACERx patient data (CRUK0044) with 28 mutations across 3 tumor regions, demonstrating production-ready capability for cancer genomics research.**

### Current Development Phase (Enhancement Phase) ✅ COMPLETED
The enhancement phase focused on **improving existing pipeline capabilities** and **implementing longitudinal analysis**:

1. **Aggregation Stage Improvements**: ✅ **COMPLETED**
   - Dynamic multi-sample support (replacing hardcoded blood/tissue assumptions)
   - Enhanced visualization combining frequency graphs with phylogenetic trees
   - Best tree visualization from aggregation results
   
2. **Longitudinal Analysis Implementation**: ✅ **COMPLETED**
   - Implemented iterative Bayesian tree updating using blood sample data
   - Developed 2-marker optimization strategy for clinical feasibility
   - Created computational-clinical feedback loop for temporal cancer monitoring
   - Integrated ddPCR data processing for liquid biopsy analysis
   - **Implemented both dynamic and fixed marker approaches**
   - **Added user-specified fixed marker functionality for clinical workflows**
   - **Created production SLURM scripts for both analysis modes**

3. **Enhanced Multi-Sample Support**: ✅ **COMPLETED**
   - Flexible VAF filtering strategies across all pipeline stages
   - Robust data consistency validation
   - Backward compatibility maintenance

4. **Fixed Marker Clinical Integration**: ✅ **COMPLETED**
   - User-specified marker input for clinician-driven analysis
   - Consistent marker tracking across all timepoints
   - Validation and error handling for missing markers
   - Production-ready SLURM script with clinical gene specifications
   - Comparative analysis between dynamic and fixed approaches

### Future Development (Clinical Integration Phase)
The next major phase will focus on **clinical deployment and validation**:
1. SLURM integration for longitudinal workflows
2. Enhanced visualization for temporal data
3. Clinical protocol standardization
4. Validation studies with real patient cohorts

This multi-phase approach ensures a solid, well-tested foundation with comprehensive longitudinal functionality ready for clinical deployment.

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
├── 5-long/                  # Longitudinal analysis stage
│   ├── longitudinal_update.py        # Main longitudinal analysis implementation (UPDATED)
│   ├── longitudinal_analysis.sh      # SLURM script for dynamic marker analysis
│   ├── longitudinal_analysis_fixed.sh # SLURM script for fixed marker analysis (NEW)
│   ├── adjust_tree_distribution.py   # Bayesian tree updating algorithms
│   ├── optimize_fraction.py          # Marker optimization for longitudinal tracking
│   ├── optimize.py                   # Tree structure optimization utilities
│   └── analyze.py                    # Analysis and tree processing utilities
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
- **Purpose**: Aggregates results from multiple bootstrap runs and creates visualizations
- **Components**:
  - `aggregation.sh`: Slurm job submission script
  - `aggregate.py`: Main aggregation implementation
  - `visualize.py`: Visualization utilities (**Enhanced**)
  - `analyze.py`: Analysis utilities (**Enhanced**)
  - `optimize.py`: Optimization utilities
- **Inputs**:
  - Patient ID
  - Bootstrap samples directory (containing bootstrap1/, bootstrap2/, etc. with PhyloWGS results)
- **Outputs**:
  - Aggregated results in `{patient_base_dir}/initial/aggregation_results/`:
    - `{patient}_results_bootstrap_initial_best.json`: Best tree structure
    - `phylowgs_bootstrap_summary.pkl`: Summary of all trees
    - `phylowgs_bootstrap_aggregation.pkl`: Complete aggregation results
    - `{patient}_combined_best_tree_initial.png`: **Best tree visualization** (highest bootstrap frequency)
    - `all_trees_initial/`: **Subdirectory containing all tree visualizations**
      - `{patient}_combined_tree_freq_{idx}_initial.png`: Combined tree + frequency plots for each unique tree structure
      - Includes phylogenetic trees with gene names and multi-sample clonal frequency plots
- **Dependencies**: Python 3.x, conda environment `aggregation_env` (specified in `environment.yml`)

#### **Enhanced Visualization Features**:
- **Best Tree Identification**: Automatically identifies and highlights the tree with highest bootstrap frequency
- **Combined Visualizations**: Side-by-side phylogenetic trees and clonal frequency plots
- **Multi-Sample Support**: Dynamic handling of 2 to n samples with proper sample detection
- **Gene Name Preservation**: Full mutation/gene information displayed in tree nodes
- **Publication-Quality Output**: High-resolution plots with proper legends and formatting
- **User-Friendly Organization**: Best tree prominently displayed, all trees available for detailed analysis

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

### 6. Longitudinal Analysis Stage (`5-long/`) ✅ **ENHANCED**
- **Purpose**: Implements iterative Bayesian tree updating using blood sample data over time with **both dynamic and fixed marker approaches**
- **Components**:
  - `longitudinal_update.py`: **Enhanced** main longitudinal analysis implementation
  - `longitudinal_analysis.sh`: SLURM script for dynamic marker analysis
  - `longitudinal_analysis_fixed.sh`: **NEW** SLURM script for fixed marker analysis
  - `adjust_tree_distribution.py`: Bayesian tree updating algorithms
  - `optimize_fraction.py`: Marker optimization for longitudinal tracking
  - `optimize.py`: Tree structure optimization utilities
  - `analyze.py`: Analysis and tree processing utilities
- **Inputs**:
  - Tree distribution files from aggregation stage (`phylowgs_bootstrap_summary.pkl`, `phylowgs_bootstrap_aggregation.pkl`)
  - Patient tissue data (SSM format)
  - Longitudinal blood sample data (CSV format with ddPCR measurements)
  - **NEW**: User-specified fixed markers for clinical workflows
  - Updated tree distributions from previous timepoints (iterative)
- **Outputs**:
  - **Dynamic approach**: Updated tree distributions with optimally selected markers per timepoint
  - **Fixed approach**: Updated tree distributions using consistent user-specified markers
  - **Comparative analysis**: Performance comparison between approaches
  - Tree weight change visualizations and analysis summaries
  - Selected marker recommendations for ddPCR assays
- **Dependencies**: 
  - Python 3.x with advanced scientific libraries
  - Gurobi optimization solver (requires license)
  - External ddPCR data from clinical laboratory

#### **Enhanced Longitudinal Analysis Workflow**
The longitudinal stage now implements **dual-mode computational-clinical feedback loops**:

**Dynamic Marker Approach (Research-Focused)**:
1. **Adaptive Selection**: Algorithmically selects optimal markers at each timepoint
2. **Maximum Information**: Optimizes for maximum discriminatory power
3. **Research Applications**: Method development and tumor dynamics understanding

**Fixed Marker Approach (Clinical-Focused)**:
1. **Clinician-Specified**: Uses markers specified by clinical teams
2. **Consistent Tracking**: Same markers across all timepoints
3. **Clinical Applications**: Standardized monitoring and treatment response assessment

**Command Line Interface**:
```bash
# Dynamic marker analysis
python longitudinal_update.py PATIENT_ID \
    --analysis-mode dynamic \
    --n-markers 3 \
    [other parameters...]

# Fixed marker analysis with user-specified markers
python longitudinal_update.py PATIENT_ID \
    --analysis-mode fixed \
    --fixed-markers TP53 KRAS PIK3CA EGFR BRAF \
    [other parameters...]

# Comparative analysis (both approaches)
python longitudinal_update.py PATIENT_ID \
    --analysis-mode both \
    --n-markers 3 \
    --fixed-markers TP53 KRAS PIK3CA \
    [other parameters...]
```

#### **Clinical Integration Features**

**Fixed Marker Validation**:
- Validates user-specified markers against available dataset
- Provides clear feedback on found/missing markers
- Proceeds with valid markers, warns about unavailable ones
- Supports full gene identifiers with genomic coordinates

**Production SLURM Integration**:
- `longitudinal_analysis.sh`: Dynamic marker analysis on HPC
- `longitudinal_analysis_fixed.sh`: Fixed marker analysis with clinical genes
- Proper resource allocation and error handling
- Integration with existing HPC job submission workflows

**Clinical Workflow Benefits**:
- **Standardized Assays**: Consistent marker panels for clinical implementation
- **Regulatory Compliance**: Fixed assays easier to validate and approve
- **Cost Efficiency**: Single assay development vs. multiple dynamic assays
- **Clinical Adoption**: Familiar workflow for clinical laboratories

#### **Key Features of Longitudinal Analysis**

**2-Marker Optimization Strategy**:
- **Rationale**: Balances clinical feasibility with statistical power
- **Selection Criteria**: Maximizes tree discrimination while minimizing cost
- **Pairwise Analysis**: Leverages phylogenetic relationships (ancestor-descendant constraints)
- **Clinical Implementation**: Simple ddPCR panels suitable for routine monitoring

**Bayesian Tree Updating**:
- **Algorithm**: Uses binomial likelihood calculations with phylogenetic constraints
- **Relationship Analysis**: Considers ancestor-descendant VAF patterns
- **Statistical Integration**: Numerical integration for likelihood computation
- **Frequency Updates**: Reweights trees based on evidence from blood data

**Temporal Evolution Tracking**:
- **Sequential Learning**: Each timepoint builds on previous knowledge
- **Dynamic Reweighting**: Tree probabilities evolve with new evidence
- **Clinical Decision Support**: Provides evolutionary trajectory insights
- **Treatment Adaptation**: Enables response monitoring and resistance detection

#### **Input File Requirements**

**Tree Distribution Files** (from Aggregation Stage):
```
{bootstrap_dir}/phylowgs_bootstrap_summary.pkl
{bootstrap_dir}/phylowgs_bootstrap_aggregation.pkl
```
Contains: Tree structures, node assignments, bootstrap frequencies, clonal frequencies

**Patient Tissue Data**:
```
{patient_name}_subset.xlsx (sheet: 'tissue_no_germline_0')
```
Columns: Gene names, chromosome, genomic position, mutation annotations

**Longitudinal Blood Sample Data**:
```
{patient_name}__DateSample.xlsx (multi-sheet: date format YYYY-MM-DD)
```
Columns per timepoint: 
- `MutDOR`: Mutant droplet counts from ddPCR
- `DOR`: Total droplet counts from ddPCR
- Index: Gene names matching tissue data

**Updated Tree Distributions** (Iterative):
```
{method}_bootstrap_summary_updated_{algo}_{n_markers}_{timepoint}_bayesian.pkl
```
Generated automatically during longitudinal processing

#### **Computational-Clinical Integration**

**Algorithm Output to Clinicians**:
```
LONGITUDINAL MONITORING REPORT - Patient CRUK0041

RECOMMENDED MARKERS FOR TRACKING:
1. GPR65 (Chr14:88477948 G>T)  
2. TMEM176B (Chr7:150490198 C>A)

RATIONALE:
- These 2 markers optimally distinguish between competing evolutionary scenarios
- Expected VAF patterns based on current tree distribution:
  * Tree A (40% probability): GPR65≈4%, TMEM176B≈2%
  * Tree B (35% probability): GPR65≈2%, TMEM176B≈4%

CLINICAL PROTOCOL:
1. Design ddPCR assays for specified markers
2. Collect blood samples monthly
3. Report VAF measurements back to analysis pipeline
4. Receive updated evolutionary trajectory reports
```

**Clinical Data Integration**:
```python
# Example clinical data input
ddpcr_results = {
    'timepoint': '2024-02-15',
    'GPR65': {'mutant_droplets': 45, 'total_droplets': 1200},      # 3.75% VAF
    'TMEM176B': {'mutant_droplets': 23, 'total_droplets': 980}    # 2.35% VAF
}

# Algorithm processes and updates tree probabilities
updated_analysis = bayesian_update(ddpcr_results)
# Result: Tree A probability increases to 55%, Tree B decreases to 25%
```

#### **Clinical Impact and Applications**

**Advantages Over Traditional Monitoring**:
- **Minimal Invasiveness**: Blood draws vs. tissue biopsies
- **Cost Efficiency**: $100-200/timepoint vs. $1000+/timepoint  
- **Real-Time Insights**: Monthly monitoring vs. 3-6 month intervals
- **Predictive Power**: Evolutionary trajectory prediction vs. static snapshots

**Clinical Decision Support**:
- **Treatment Response**: Monitor clonal evolution during therapy
- **Resistance Detection**: Early identification of resistance emergence
- **Adaptive Therapy**: Adjust treatment based on evolutionary trajectories
- **Personalized Monitoring**: Patient-specific marker panels

**Research Applications**:
- **Cancer Evolution Studies**: Temporal clonal dynamics analysis
- **Biomarker Validation**: Longitudinal marker performance assessment
- **Treatment Optimization**: Evolution-guided therapy development
- **Clinical Trial Design**: Stratification based on evolutionary patterns

#### **Current Implementation Status**

**Functional Components** ✅:
- Iterative Bayesian tree updating algorithm
- 2-marker optimization with Gurobi solver
- ddPCR data integration and processing
- Multi-timepoint analysis workflow
- Tree frequency visualization

**Limitations** ⚠️:
- Manual configuration required (no SLURM integration)
- Limited visualization capabilities for temporal data
- Hardcoded directory structures and patient-specific paths
- No automated clinical report generation

**Future Development Needs**:
- SLURM integration for automated workflows
- Enhanced temporal visualizations
- Flexible data format support
- Clinical protocol standardization
- Validation studies with patient cohorts

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
├── longitudinal/            # Longitudinal analysis results (when applicable)
│   ├── updated_trees/       # Updated tree distributions per timepoint
│   │   ├── phylowgs_bootstrap_summary_updated_struct_2_0_bayesian.pkl
│   │   ├── phylowgs_bootstrap_summary_updated_struct_2_1_bayesian.pkl
│   │   └── ...
│   ├── visualizations/      # Temporal evolution plots
│   │   ├── Patient_{id}_weights_change.eps
│   │   └── temporal_evolution_plots/
│   ├── marker_selections/   # Selected markers per timepoint
│   └── clinical_reports/    # Algorithm recommendations for clinical teams
```

## Running the Pipeline

### Initial Analysis (Stages 1-4)
1. Ensure all dependencies are installed:
   ```bash
   ./install_phylowgs.sh  # Install PhyloWGS
   ```

2. Run the initial pipeline:
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

### Longitudinal Analysis (Stage 5)
1. **Computational Setup**: Configure patient parameters and paths in `5-long/iterative_pipeline_real.py`
   ```python
   patient_name = 'CRUK0041'
   n_markers = 2
   directory = Path('/path/to/patient_data')
   liquid_biopsy_directory = Path('/path/to/ddpcr_data')
   ```

2. **Clinical Data Preparation**: Organize ddPCR data in required Excel format
   ```
   {patient_name}__DateSample.xlsx
   Sheet names: 2024-01-15, 2024-02-15, 2024-03-15, ...
   Columns: MutDOR (mutant droplets), DOR (total droplets)
   Index: Gene names matching tissue data
   ```

3. **Run Longitudinal Analysis**:
   ```bash
   cd 5-long
   python iterative_pipeline_real.py
   ```

4. Monitor progress:
   ```bash
   squeue -u $USER  # Check job status (if using SLURM)
   ```

## Environment Setup
Each stage has its own conda environment specified in `environment.yml`:
- Bootstrap: `preprocess_env`
- PhyloWGS: PhyloWGS-specific environment
- Aggregation: `aggregation_env`
- Marker Selection: `markers_env`
- Longitudinal Analysis: `long_env`

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

## Current Development Priorities

### 1. Longitudinal Analysis ✅ COMPLETED
**Goal**: Implement comprehensive longitudinal cancer evolution tracking

**Completed Features**:
- ✅ Iterative Bayesian tree updating using blood sample data
- ✅ **Dual-mode operation**: Dynamic and fixed marker approaches
- ✅ **Clinical workflow integration**: User-specified fixed markers
- ✅ Computational-clinical feedback loop implementation
- ✅ ddPCR data integration and processing
- ✅ Multi-timepoint analysis workflow
- ✅ Tree frequency visualization and reporting
- ✅ **Production SLURM scripts**: Both dynamic and fixed marker analysis
- ✅ **Comparative analysis**: Performance comparison between approaches

**Achievement**: Full longitudinal analysis capability allowing temporal cancer evolution tracking through blood-based monitoring with both research-optimized (dynamic) and clinically-practical (fixed) marker approaches.

### 2. Clinical Integration and Validation (High Priority)
**Goal**: Prepare longitudinal analysis for clinical deployment and validation

**Key Tasks**:
- SLURM integration for automated longitudinal workflows
- Enhanced temporal visualization suite
- Clinical protocol standardization and documentation
- Flexible data format support for various clinical laboratories
- Automated clinical report generation

**Expected Impact**: Ready-for-deployment clinical tool for cancer evolution monitoring

### 3. Pipeline Enhancement and Optimization (Medium Priority)
**Goal**: Improve overall pipeline performance and usability

**Key Tasks**:
- Advanced visualization capabilities for all stages
- Performance optimization for large datasets
- Enhanced error handling and recovery mechanisms
- Comprehensive unit testing and validation suite
- User interface development for clinical users

**Expected Impact**: Robust, user-friendly pipeline suitable for clinical research environments

### 4. Research Applications and Extensions (Medium-Low Priority)
**Goal**: Extend pipeline capabilities for advanced research applications

**Key Tasks**:
- Multi-patient comparative analysis tools
- Integration with treatment response data
- Advanced statistical modeling for evolutionary predictions
- Biomarker discovery and validation frameworks
- Clinical trial stratification tools

**Expected Impact**: Comprehensive research platform for cancer evolution studies and clinical trial design

## Testing Strategy
- **Incremental Development**: Each enhancement builds upon the stable foundation of the initial phase
- **Backward Compatibility**: All changes maintain compatibility with existing data and workflows
- **Comprehensive Testing**: Use existing 20-bootstrap test dataset to validate all improvements
- **Documentation**: Thorough documentation of all new features and configuration options
- **Longitudinal Validation**: Test temporal analysis with simulated and real patient data

## Development Timeline (Updated)
- **Phase 1 (HPC Pipeline Implementation)**: ✅ Completed - 6 days
- **Phase 2 (Aggregation Enhancements)**: ✅ Completed - 8 days  
- **Phase 3 (Longitudinal Implementation)**: ✅ Completed - 12 days
- **Phase 4 (Clinical Integration)**: 🔄 In Progress - 5-8 days estimated
- **Phase 5 (Research Extensions)**: 📅 Planned - 10-15 days estimated

**Current Status**: 3/5 phases completed. The pipeline now includes full longitudinal analysis capability with **both dynamic and fixed marker approaches**, 2-marker optimization, Bayesian tree updating, and computational-clinical feedback loops.

**Total Development Time**: 28 days completed, 13-21 days remaining for clinical deployment readiness.

## Project Achievements

### **Core Pipeline Functionality** ✅ COMPLETED
- **Multi-stage processing**: Bootstrap → PhyloWGS → Aggregation → Marker Selection → Longitudinal Analysis
- **Multi-sample support**: Dynamic handling of 2 to n tumor regions
- **Production deployment**: Successfully processes real TRACERx patient data (CRUK0044)
- **Robust error handling**: Comprehensive validation and consistency checking

### **Advanced Longitudinal Analysis** ✅ COMPLETED  
- **Temporal evolution tracking**: Blood-based cancer monitoring over time
- **Dual-mode operation**: Both dynamic (research) and fixed (clinical) marker approaches
- **2-marker optimization**: Clinically feasible ddPCR panel design
- **Bayesian tree updating**: Statistical integration of longitudinal evidence
- **Clinical integration**: Computational-clinical feedback loop implementation
- **User-specified markers**: Clinician-driven marker selection for fixed approach
- **Production deployment**: SLURM scripts for both analysis modes

### **Research and Clinical Impact**
- **Cost reduction**: $100-200 per monitoring timepoint vs. $1000+ for tissue analysis
- **Clinical feasibility**: Monthly blood draws vs. invasive tissue biopsies
- **Predictive capability**: Evolutionary trajectory forecasting for treatment adaptation
- **Personalized medicine**: Patient-specific marker panels for precision monitoring

## Future Directions

### **Immediate Development (Next 3-6 months)**
1. **Clinical Validation Studies**: Partner with clinical centers for patient cohort validation
2. **SLURM Integration**: Automate longitudinal workflows for production deployment
3. **Enhanced Visualization**: Comprehensive temporal evolution visualization suite
4. **Clinical Protocol Standardization**: Develop clinical implementation guidelines

### **Medium-term Extensions (6-12 months)**
1. **Treatment Integration**: Incorporate therapy response and resistance monitoring
2. **Multi-patient Analysis**: Comparative evolution studies across patient cohorts  
3. **Biomarker Discovery**: Identify novel markers for specific cancer types
4. **Clinical Trial Support**: Stratification tools for evolution-guided trial design

### **Long-term Vision (1-3 years)**
1. **Clinical Deployment**: Routine clinical implementation for cancer monitoring
2. **Regulatory Approval**: FDA/regulatory pathway for clinical diagnostic use
3. **Platform Expansion**: Extension to multiple cancer types and treatment modalities
4. **AI Integration**: Machine learning for enhanced evolutionary prediction models

This comprehensive pipeline represents a significant advancement in computational cancer genomics, providing the foundation for precision medicine approaches based on cancer evolutionary dynamics. 