# TracerX Pipeline Implementation Roadmap

## Current Tickets

### 1. Create Small Data Subset From SSM.txt
**Goal**: Generate a small test dataset with fewer than 5 genes to enable testing on limited resources

**Tasks**:
- [x] Extract 5 mutations from each node of known tree for CRUK0044 from `data/ssm.txt` 
- [x] Save as `data/ssm_subset.txt` 
- [ ] Validate the subset file format

```bash
# Command to create a subset with first 5 mutations (header + 5 data rows)
head -n 6 data/ssm.txt > data/ssm_small.txt
```

### 2. Get Main_Init.sh Working Through Non-Longitudinal Stage
**Goal**: Successfully run the initial pipeline with the small dataset on Guorbi free tier

**Debugging Tasks**:
- [ ] Verify all conda environments can be properly activated
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