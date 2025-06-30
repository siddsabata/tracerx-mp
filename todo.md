# TracerX Marker Selection Pipeline - Steps 1-4 Enhancement

## Project Objective
Focus on cleaning up, enhancing, and streamlining steps 1-4 of the TracerX marker selection pipeline while preserving all existing functionality. The goal is to create a unified, YAML-configured, and orchestrated workflow for the initial processing phases.

## Core Principles
- **Preserve functionality**: Steps 1-4 currently work fine - maintain exact same behavior
- **Simplest solution**: Follow first principles, avoid over-engineering
- **Clean code**: Files should be no more than 300 lines (except master sbatch script and bash scripts)
- **Consistent structure**: Unified approach across all 4 steps

## Task Breakdown

### 1. Code Cleanup and Organization ⚠️ CRITICAL PRIORITY
**Objective**: Clean up all code in steps 1-4 while preserving exact functionality

#### 1.1 File Structure Reorganization
- [ ] Review current file naming conventions across all 4 steps
- [ ] Rename files appropriately for consistency (e.g., `bootstrap.py` → `step1_bootstrap.py`)
- [ ] Consolidate redundant utility functions across steps
- [ ] Remove unused/obsolete files while maintaining functionality
- [ ] Ensure each Python file is under 300 lines

#### 1.2 Code Quality Improvements
- [ ] Add comprehensive comments and docstrings to all Python files
- [ ] Standardize import statements and coding style
- [ ] Remove hardcoded paths and make configuration-driven
- [ ] Improve error handling and logging consistency
- [ ] Add input validation for all functions

#### 1.3 Dependency Management
- [ ] Review and clean up environment.yml files for each step
- [ ] Remove unused dependencies
- [ ] Ensure version consistency across steps
- [ ] Document all external dependencies clearly

### 2. YAML Configuration System ⚠️ HIGH PRIORITY
**Objective**: Implement unified YAML configuration for steps 1-4 (similar to step 5)

#### 2.1 YAML Schema Design
- [ ] Create comprehensive YAML schema for all 4 steps
- [ ] Design configuration structure covering:
  - Patient information
  - Input/output directories
  - Bootstrap parameters
  - PhyloWGS settings
  - Aggregation options
  - Marker selection criteria
- [ ] Create template YAML files for different use cases

#### 2.2 Configuration Integration
- [ ] Modify step 1 (bootstrap) to accept YAML configuration
- [ ] Modify step 2 (phylowgs) to accept YAML configuration
- [ ] Modify step 3 (aggregation) to accept YAML configuration
- [ ] Modify step 4 (markers) to accept YAML configuration
- [ ] Implement configuration validation for each step
- [ ] Maintain backward compatibility with current CLI arguments

#### 2.3 Configuration Templates
- [ ] Create `configs/` directory structure
- [ ] Design template: `configs/standard_analysis.yaml`
- [ ] Design template: `configs/test_analysis.yaml` (for 5-mutation subset)
- [ ] Design template: `configs/high_depth_analysis.yaml`
- [ ] Add configuration documentation and examples

### 3. Master SLURM Orchestration Script ⚠️ HIGH PRIORITY
**Objective**: Create single sbatch command to run entire steps 1-4 pipeline

#### 3.1 Master Script Development
- [ ] Create `master_pipeline.sh` - single entry point for steps 1-4
- [ ] Implement proper SLURM job dependencies (step N+1 waits for step N)
- [ ] Design job array for step 2 (phylowgs) to handle multiple bootstraps
- [ ] Add proper resource allocation for each step
- [ ] Implement comprehensive error handling and rollback

#### 3.2 Job Dependency Management
- [ ] Step 1 (bootstrap): Single job, creates bootstrap samples
- [ ] Step 2 (phylowgs): Job array, processes all bootstrap samples in parallel
- [ ] Step 3 (aggregation): Single job, depends on all step 2 jobs completing
- [ ] Step 4 (markers): Single job, depends on step 3 completion
- [ ] Add proper exit code handling and dependency checking

#### 3.3 Resource Optimization
- [ ] Optimize memory and CPU allocation for each step
- [ ] Implement intelligent walltime estimation based on data size
- [ ] Add queue selection logic based on job requirements
- [ ] Create monitoring and progress reporting

### 4. Documentation Creation ⚠️ MEDIUM PRIORITY
**Objective**: Create comprehensive `initial.md` documentation for steps 1-4

#### 4.1 Technical Documentation
- [ ] Create `initial.md` following similar structure to `project.md`
- [ ] Document each step's purpose, inputs, outputs, and dependencies
- [ ] Include YAML configuration examples and explanations
- [ ] Add troubleshooting guide for common issues

#### 4.2 User Guide
- [ ] Create step-by-step usage instructions
- [ ] Document YAML configuration options
- [ ] Add examples for different analysis scenarios
- [ ] Include performance optimization tips

#### 4.3 Developer Guide
- [ ] Document code structure and organization
- [ ] Add contribution guidelines
- [ ] Include testing procedures
- [ ] Document extension points for future development

## Implementation Strategy

### Phase 1: Foundation (Days 1-2)
1. **Code audit**: Review all files in steps 1-4, identify cleanup opportunities
2. **Preserve functionality**: Create comprehensive test cases to ensure no regression
3. **File organization**: Rename and reorganize files for consistency

### Phase 2: YAML Integration (Days 3-4)
1. **Schema design**: Create comprehensive YAML configuration schema
2. **Step-by-step integration**: Modify each step to accept YAML configuration
3. **Template creation**: Develop YAML templates for common use cases

### Phase 3: Master Orchestration (Days 5-6)
1. **Master script development**: Create single-command pipeline execution
2. **Dependency management**: Implement proper SLURM job dependencies
3. **Resource optimization**: Optimize resource allocation and job arrays

### Phase 4: Documentation (Days 7-8)
1. **Technical documentation**: Create comprehensive `initial.md`
2. **User guides**: Document configuration and usage
3. **Testing validation**: Ensure all functionality works as expected

## Success Criteria

### Functional Requirements
- [ ] All existing functionality preserved (steps 1-4 work exactly as before)
- [ ] Single YAML file configures entire steps 1-4 pipeline
- [ ] Single `sbatch master_pipeline.sh config.yaml` command runs complete pipeline
- [ ] Job dependencies work correctly (no step starts until previous completes)
- [ ] Resource allocation optimized for each step

### Quality Requirements
- [ ] All Python files under 300 lines
- [ ] Comprehensive comments and documentation
- [ ] Clean, consistent code structure
- [ ] Robust error handling and validation
- [ ] Backward compatibility maintained

### Documentation Requirements
- [ ] Complete `initial.md` documentation
- [ ] YAML configuration guide
- [ ] Usage examples and tutorials
- [ ] Troubleshooting guide

## Testing Plan

### Functionality Testing
- [ ] Test with existing CRUK0044 dataset (28 mutations)
- [ ] Test with 5-mutation subset for rapid validation
- [ ] Compare outputs with current pipeline results
- [ ] Validate all intermediate files and final outputs

### Configuration Testing
- [ ] Test YAML configuration validation
- [ ] Test error handling for invalid configurations
- [ ] Test backward compatibility with CLI arguments
- [ ] Test different configuration templates

### Orchestration Testing
- [ ] Test master script with small dataset
- [ ] Test job dependency chain
- [ ] Test failure recovery and rollback
- [ ] Test resource allocation and monitoring

## Notes
- **Preserve existing behavior**: This is the most critical requirement
- **Incremental approach**: Make small, testable changes
- **Comprehensive testing**: Validate every change against existing outputs
- **Clean implementation**: Follow established patterns from step 5 YAML system
- **User experience**: Single command should handle entire pipeline execution
