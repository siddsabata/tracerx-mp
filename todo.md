# TracerX Pipeline Implementation Roadmap

## Current Tickets

### 1. Create Small Data Subset From SSM.txt
**Goal**: Generate a small test dataset with fewer than 5 genes to enable testing on limited resources

**Tasks**:
- [x] Extract 5 mutations from each node of known tree for CRUK0044 from `data/ssm.txt` 
- [x] Save as `data/ssm_subset.txt` 
- [x] Validate the subset file format

### 2. Get Main_Init.sh Working Through Non-Longitudinal Stage
**Goal**: Successfully run the initial pipeline with the small dataset on Guorbi free tier

**Debugging Tasks**:
- [x] Verify all conda environments can be properly activated
  - Check each environment.yml file in the component directories
  - Ensure conda is properly set up on the Guorbi platform
  
- [ ] Test each stage individually before running the full pipeline:
  ```bash
  # Test bootstrap stage directly
  cd 1-bootstrap
  bash bootstrap.sh ../../data/ssm_small.txt /path/to/output 5
  
  # Test phylowgs stage directly
  cd 2-phylowgs
  bash phylowgs.sh /path/to/output/bootstraps
  
  # And so on for each stage
  ```
  - [ ] Ongoing Gurobi licensing issues:
    - Identified that the cluster has Gurobi 9.0.2 available via module system (`module load gurobi902`)
    - Modified the markers_env conda environment to only install the gurobipy Python interface
    - Updated marker_selection.sh to load the Gurobi module and verify it's accessible from Python
    - Added verification steps to ensure compatibility between the Python interface and the system Gurobi
    - Still encountering issues with Gurobi licensing - need to troubleshoot further
    - Potential next steps:
      - Check if gurobipy version matches the module version
      - Verify license file location and permissions
      - Try running a simple Gurobi test script to isolate the issue
      - Consider using the simplified optimization function as a workaround

- [x] Fix path resolution issues in component scripts
  - **Problem**: Scripts were failing due to SLURM changing the working directory, causing relative paths to break
  - **Initial Solution**: Modified component scripts to convert relative paths to absolute paths
  - **Improved Solution**: Moved all path conversion to the main script (main_init.sh):
    - All input paths are now converted to absolute at the beginning of main_init.sh
    - Path conversion logic was removed from all component scripts (bootstrap.sh, phylowgs.sh, etc.)
    - This prevents issues when component scripts try to convert paths based on their own working directory
  - **Path Detection Method**: 
    - The scripts detect absolute paths by checking if they start with a forward slash `/`
    - This works on Unix/Linux/MacOS where absolute paths always begin with `/`
    - This implementation is specific to Unix-like systems (such as the Guorbi HPC)
    - If the pipeline needs to run on Windows in the future, this detection would need to be modified to handle Windows-style paths (e.g., `C:\path\to\file`)

- [ ] Modify resource requirements if needed:
  - Review `#SBATCH` directives in each stage's shell script
  - Reduce memory and CPU requests to fit within Guorbi free tier limits
  
- [ ] Run the pipeline with small dataset:
  ```bash
  bash main_init.sh TEST_PATIENT data/ssm_small.txt /path/to/output 5 1500
  ```

- [ ] Check logs for errors and fix each issue:
  - Path issues
  - Dependency issues
  - Resource limitations
  - Environment activation problems

### 3. Develop Longitudinal Update Functionality
**Goal**: Implement the functionality to update tree distributions with longitudinal data

**Implementation Tasks**:
- [ ] Design the data format for longitudinal blood samples
- [ ] Create a new module for processing longitudinal ddPCR data
  - Directory structure: `5-longitudinal/`
  - Files needed:
    - `longitudinal_update.sh`: Slurm job submission script
    - `longitudinal_update.py`: Python implementation
    - `environment.yml`: Conda environment for longitudinal processing
    
- [ ] Implement methods to:
  - Process ddPCR data from blood samples
  - Update the existing tree structures
  - Recalculate clonal fractions
  - Track changes over time
  
- [ ] Test with simulated longitudinal data

### 4. Incorporate Longitudinal Updates into an Automated Script
**Goal**: Create a second master script for orchestrating longitudinal updates

**Implementation Tasks**:
- [ ] Create `longitudinal_init.sh` script modeled after `main_init.sh`
- [ ] Structure the script to:
  - Accept parameters:
    - Patient ID
    - Initial results directory
    - Longitudinal data file(s)
    - Time points
  - Create appropriate directory structure for longitudinal results
  - Submit jobs with proper dependencies
  
- [ ] Implement robust error handling and logging
- [ ] Test with simulated longitudinal data
- [ ] Document the longitudinal update process

## Testing Methodology
For each stage of implementation:
1. Start with minimal test cases
2. Log intermediate outputs extensively
3. Validate outputs against expected results
4. Only proceed to the next stage when current stage is stable

## Resources Required
- Slurm cluster access (Guorbi)
- Conda environment management
- Patient data (small subset initially)
- Additional storage for longitudinal results

## Timeline Estimate
- Ticket 1: 1 day
- Ticket 2: 3-5 days
- Ticket 3: 7-10 days 
- Ticket 4: 3-5 days

Total: 14-21 days depending on complexity of issues encountered 