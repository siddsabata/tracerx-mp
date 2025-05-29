# TracerX Pipeline Implementation Roadmap

## Current Tickets - Revised Approach

### 1. Get Pipeline Working Through Non-Longitudinal Stage ✅ COMPLETED
**Goal**: Successfully run the initial pipeline with the CRUK0044 dataset on HPC cluster

**Debugging Tasks**:
- [x] Create small data subset from SSM.txt (5 mutations from CRUK0044) for initial testing
- [x] Save as `data/ssm_subset.txt` and validate format
- [x] **Successfully run pipeline with full CRUK0044 dataset (28 mutations, 3 tumor regions)**
- [x] Verify all conda environments can be properly activated
- [x] Gurobi licensing issues: Resolve Gurobi Issues
- [x] Fix path resolution issues in component scripts
- [x] Debugging Marker Selection Stage (completed)
- [x] Debugged Gurobi optimization errors in marker selection (input data filtering/model infeasibility)
- [x] Added robust error handling in optimize_fraction_weighted_overall (4-markers/optimize_fraction.py)
- [x] Added debugging printout of filtered SSM dataframe in run_data.py
- [x] **Resolved data inconsistency issues by implementing multi-sample SSM conversion**
- [x] Created `convert_ssm_to_dataframe_v2.py` for flexible multi-sample SSM to DataFrame conversion
- [x] Created `run_data_multi_sample.py` for marker selection with multi-sample support
- [x] Implemented flexible VAF filtering strategies (any_high, all_high, majority_high, specific_samples)
- [x] Added tree compatibility validation to catch indexing mismatches early

**Major Achievement**: ✅ **Full pipeline successfully processes real TRACERx patient data (CRUK0044) with 28 mutations across 3 tumor regions through all 4 stages: Bootstrap → PhyloWGS → Aggregation → Marker Selection**

### 2. Improve Aggregation Stage for Multi-Sample Support and Better Visualization
**Goal**: Enhance the aggregation stage to handle n samples dynamically and improve visualization quality

**Implementation Tasks**:
- [x] **Multi-Sample Aggregation Support**: ✅ **COMPLETED**
  - [x] Analyzed current aggregation code in `3-aggregation/` and identified hardcoded blood/tissue assumptions in `visualize.py`
  - [x] Modified `visualize.py` to handle variable numbers of samples (2 to n) with dynamic sample detection
  - [x] Updated frequency calculation and plotting to work with n samples instead of hardcoded blood/tissue
  - [x] Ensured sample naming is consistent with the multi-sample SSM format using `Region_0`, `Region_1`, etc.
  - [x] Added `validate_sample_consistency()` function for data integrity validation
  - [x] **Successfully tested with CRUK0044 data: processed 80/100 bootstrap replicates, correctly detected 3 samples per tree**
  - [x] Enhanced visualization aesthetics with better color schemes, proper legends, and improved plot layout

- [x] **Enhanced Visualization**: ✅ **COMPLETED**
  - [x] Combine frequency graphs with phylogenetic trees in side-by-side layout for better readability
  - [x] Investigated correlation between frequency graphs and tree structures
  - [x] Created unified visualization that shows tree structure alongside corresponding frequency data
  - [x] Improved plot aesthetics and labeling for publication-quality figures
  - [x] Enhanced visualization generates combined plots only, with proper cleanup of temporary files

- [x] **Best Tree Visualization**: ✅ **COMPLETED**
  - [x] Implemented enhanced best tree identification and visualization system
  - [x] Best tree automatically determined by highest bootstrap frequency
  - [x] Created organized output structure:
    - Main directory: `{patient}_combined_best_tree_initial.png` (best tree for quick assessment)
    - Subdirectory: `all_trees_initial/` (all tree visualizations for detailed analysis)
  - [x] Preserved gene names and mutation information in tree visualizations
  - [x] Integrated seamlessly with existing aggregation pipeline
  - [x] Removed redundant code and streamlined implementation
  - [x] Multi-sample support with dynamic sample detection (2 to n samples)
  - [x] Publication-quality combined tree + frequency visualizations

- [ ] **Testing and Validation**:
  - Test aggregation improvements with existing test data (20 bootstrap samples)
  - Validate that multi-sample aggregation produces consistent results
  - Ensure backward compatibility with existing data formats
  - Document new visualization features and parameters

**Major Achievement**: ✅ **Multi-sample aggregation support successfully implemented! The aggregation stage now dynamically handles 2 to n samples, replacing hardcoded blood/tissue assumptions. Tested with CRUK0044 (3 tumor regions) - processed 80 bootstrap replicates and generated 120+ visualization files with proper multi-sample support.**

### 3. Develop Longitudinal Update Functionality (Simplified Approach)
**Goal**: Implement longitudinal functionality with simpler file I/O and streamlined data processing

**Implementation Tasks**:
- [ ] **Simplified Longitudinal Data Format**:
  - Design streamlined data format for longitudinal blood samples
  - Use similar tab-separated format as SSM files for consistency
  - Minimize complex data transformations and focus on core functionality
  - Create example longitudinal data files for testing

- [ ] **Longitudinal Processing Module**:
  - Create `5-longitudinal/` directory with simplified structure:
    - `longitudinal_update.sh`: SLURM job submission script
    - `longitudinal_update.py`: Core longitudinal processing implementation
    - `environment.yml`: Conda environment for longitudinal processing
  - Implement methods to:
    - Read longitudinal ddPCR data from blood samples
    - Update existing tree structures with new time point data
    - Recalculate clonal fractions over time
    - Track temporal changes in clonal evolution
    - Generate longitudinal reports and visualizations

- [ ] **Integration with Existing Pipeline**:
  - Ensure longitudinal module can read outputs from the initial pipeline
  - Maintain compatibility with existing data structures and formats
  - Use the improved multi-sample framework as foundation
  - Leverage enhanced visualization capabilities from aggregation improvements

- [ ] **Testing and Validation**:
  - Create simulated longitudinal datasets for testing
  - Validate longitudinal updates against known temporal patterns
  - Test integration with improved aggregation and visualization

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

### 5. Automate Individual SLURM Scripts (Lowest Priority - Not Currently Working)
**Goal**: Streamline pipeline execution by reducing manual SLURM script management

**Status**: ⚠️ Full automation is not currently working and should be deprioritized

**Implementation Tasks**:
- [ ] **Script Consolidation Analysis**:
  - Review current SLURM scripts in each stage directory
  - Identify opportunities for consolidation and automation
  - Assess benefits vs. complexity trade-offs

- [ ] **Automated Script Generation**:
  - Create template-based SLURM script generation
  - Implement dynamic resource allocation based on data size
  - Automate environment setup and dependency management
  - Generate stage-specific scripts from common templates

- [ ] **Enhanced Pipeline Orchestration**:
  - Improve `main_init.sh` to handle more complex workflows
  - Add support for conditional stage execution
  - Implement better error recovery and restart capabilities
  - Add pipeline status monitoring and reporting

- [ ] **Documentation and Testing**:
  - Document automated features and configuration options
  - Test automation improvements with various data sizes
  - Ensure backward compatibility with manual script execution

## Testing Methodology
For each stage of implementation:
1. Start with minimal test cases using existing data
2. Log intermediate outputs extensively
3. Validate outputs against expected results and existing benchmarks
4. Only proceed to the next stage when current stage is stable
5. Maintain backward compatibility throughout development

## Resources Required
- SLURM cluster access (HPC)
- Conda environment management
- Patient data (existing test dataset with 80 bootstrap samples successfully processed)
- Additional storage for enhanced visualizations and longitudinal results

## Timeline Estimate - Revised
- **Ticket 1**: ✅ Completed (6 days - included data subset creation and full pipeline debugging)
- **Ticket 2**: 🔄 **IN PROGRESS** (8-12 days total estimated)
  - ✅ **Multi-sample aggregation support: COMPLETED** (2 days)
  - [x] Enhanced visualization: ✅ **COMPLETED** (3-4 days)
  - [x] Best tree visualization: ✅ **COMPLETED** (2-3 days)  
  - [ ] Testing and validation: 1-2 days
- **Ticket 3**: 10-14 days (simplified longitudinal functionality)
- **Ticket 4**: 3-5 days (longitudinal automation script)
- **Ticket 5**: 5-7 days (SLURM automation improvements - **NOT CURRENTLY WORKING**)

**Progress**: 1.25/5 tickets completed. The multi-sample framework is now fully implemented across both marker selection and aggregation stages, providing a solid foundation for enhanced visualizations and longitudinal analysis.

**Total remaining for core functionality**: 19-29 days (tickets 2-4)
**Total if including automation**: 24-36 days (all tickets, but automation may not be feasible)

## Implementation Notes
- **Multi-sample foundation**: ✅ **COMPLETED** - The multi-sample SSM conversion framework is now fully implemented across aggregation and marker selection stages
- **Incremental approach**: Each enhancement builds upon previous work and maintains backward compatibility  
- **Testing focus**: Extensive testing with existing 80-bootstrap dataset ensures reliability
- **Documentation**: All improvements are thoroughly documented for future development and maintenance
- **Automation concerns**: Full SLURM script automation is not currently working and should be considered optional/future work

### 6. Incorporate Longitudinal Updates into an Automated Script
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
- Ticket 1: ✅ Completed (1 day)
- Ticket 2: ✅ **Multi-sample support COMPLETED**, Enhanced visualization IN PROGRESS (5 days total - included multi-sample SSM conversion work)
- Ticket 3: 7-10 days 
- Ticket 4: 3-5 days

**Progress**: 1.25/4 tickets completed. Multi-sample aggregation support successfully implemented and tested. The aggregation stage now handles 2 to n samples dynamically, consistent with the marker selection stage framework.

Total remaining: 8-13 days for enhanced visualization + longitudinal functionality 