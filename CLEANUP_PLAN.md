# TracerX-MP Repository Cleanup Plan

## Overview
This document outlines the systematic cleanup and restructuring of the TracerX-MP repository to improve organization while maintaining 100% functionality.

## Current Issues
1. **Confusing numbered directories** (1-bootstrap, 2-phylowgs, etc.) - not intuitive
2. **Scattered documentation** files at root level
3. **Mixed naming conventions** (step3_aggregate.py vs aggregate.py)
4. **Data/code separation** issues
5. **File duplication** (analyze.py in multiple directories)
6. **Inconsistent structure** across pipeline stages

## Proposed New Structure

```
tracerx-mp/
├── README.md                           # Main documentation (consolidated)
├── setup/                              # Installation and setup
│   ├── install_phylowgs.sh            # Moved from root
│   └── environment_setup.md            # New setup guide
├── src/                                # All source code organized by function
│   ├── bootstrap/                      # Stage 1: Bootstrap sampling
│   │   ├── bootstrap.py               # Renamed from step1_bootstrap.py
│   │   ├── bootstrap.sh
│   │   └── environment.yml
│   ├── phylowgs/                       # Stage 2: Phylogenetic inference
│   │   ├── phylowgs.sh
│   │   └── environment.yml
│   ├── aggregation/                    # Stage 3: Result aggregation
│   │   ├── aggregate.py               # Renamed from step3_aggregate.py
│   │   ├── analyze.py                 # Consolidated from duplicates
│   │   ├── optimize.py
│   │   ├── tree_operations.py
│   │   ├── tree_rendering.py
│   │   ├── visualization.py           # Renamed from step3_visualization.py
│   │   ├── aggregation.sh
│   │   └── environment.yml
│   ├── markers/                        # Stage 4: Marker selection
│   │   ├── marker_selection.py        # Consolidated and renamed
│   │   ├── optimize_fraction.py
│   │   ├── convert_ssm.py             # Renamed from step4_convert_ssm.py
│   │   ├── marker_selection.sh
│   │   └── environment.yml
│   ├── longitudinal/                   # Stage 5: Longitudinal analysis
│   │   ├── longitudinal_main.py       # Main entry point
│   │   ├── config_handler.py
│   │   ├── data_loader.py
│   │   ├── fixed_analysis.py
│   │   ├── dynamic_analysis.py
│   │   ├── marker_validator.py
│   │   ├── tree_updater.py
│   │   ├── output_manager.py
│   │   ├── utils.py
│   │   ├── longitudinal_analysis.sh
│   │   └── environment.yml
│   └── shared/                         # Shared utilities (new)
│       ├── common.py                   # Common functions
│       └── validation.py               # Input validation
├── pipelines/                          # Main orchestration scripts
│   ├── master_pipeline.sh             # Moved from root
│   ├── multi_patient_pipeline.sh      # Moved from root
│   └── pipeline_utils.sh              # New helper functions
├── configs/                            # Configuration files
│   ├── templates/                      # Template configurations
│   │   ├── standard_analysis.yaml
│   │   ├── test_analysis.yaml
│   │   ├── high_depth_analysis.yaml
│   │   ├── multi_patient.yaml
│   │   └── multi_patient_test.yaml
│   └── examples/                       # Example configurations
│       ├── cruk0044_fixed.yaml
│       └── cruk0044_dynamic.yaml
├── data/                               # Sample and test data
│   ├── examples/                       # Small example datasets
│   │   ├── ssm.txt
│   │   ├── ssm_subset.txt
│   │   └── cruk0044_liquid.csv
│   └── test_patients/                  # Test patient data
│       └── [existing test files]
├── batch_data/                         # Large batch datasets
│   └── ahn_june2023/                   # Renamed from new_ahn_june2023
│       ├── batch_0/
│       ├── batch_1/
│       └── [other batches]
└── docs/                               # All documentation
    ├── README_CONFIGURATION.md
    ├── README_MULTI_PATIENT.md
    ├── PIPELINE_IMPLEMENTATION.md
    ├── VISUALIZATION_SUMMARY.md
    └── project_overview.md             # Renamed from project.md
```

## Implementation Steps

### Phase 1: Create New Directory Structure
1. Create `src/`, `pipelines/`, `setup/`, `docs/`, `batch_data/` directories
2. Create subdirectories within `src/` for each pipeline stage
3. Reorganize `configs/` with `templates/` and `examples/` subdirectories

### Phase 2: Move and Rename Files
1. Move numbered directories (1-bootstrap → src/bootstrap)
2. Rename files for consistency (step1_bootstrap.py → bootstrap.py)
3. Move scripts to appropriate locations (master_pipeline.sh → pipelines/)
4. Move documentation to `docs/` directory

### Phase 3: Update Path References
1. Update shell scripts with new paths
2. Update Python imports where necessary
3. Update configuration files with new paths
4. Update documentation with new structure

### Phase 4: Consolidate and Deduplicate
1. Remove duplicate files (multiple analyze.py files)
2. Consolidate similar functionality
3. Create shared utilities in `src/shared/`

### Phase 5: Final Validation
1. Test all entry points work correctly
2. Validate all imports resolve
3. Test sample configurations
4. Update README with new structure

## Key Benefits

1. **Intuitive Structure**: Clear functional organization instead of numbers
2. **Reduced Confusion**: All source code in `src/`, all docs in `docs/`
3. **Better Separation**: Code, configs, data, and docs clearly separated
4. **Consistent Naming**: Uniform file naming conventions
5. **Easier Navigation**: Logical hierarchy for developers
6. **Maintainability**: Cleaner structure for future development

## Compatibility Guarantees

- **100% Functional Compatibility**: All existing workflows will continue to work
- **Path Updates**: All scripts updated to reference new locations
- **Entry Points Preserved**: `master_pipeline.sh` and other entry points maintained
- **Configuration Compatibility**: Existing YAML configs will work with path updates

## Risk Mitigation

- **Incremental Changes**: Move and test one component at a time
- **Path Validation**: Ensure all references are updated correctly
- **Testing**: Validate each stage works after restructuring
- **Backup**: Original structure preserved during transition