# TracerX Longitudinal Analysis Cleanup TODO

## Overview
Clean up the longitudinal analysis pipeline to follow first principles with simple, focused functionality. Remove placeholder features and unnecessary complexity.

## 1. Code Structure Refactoring (Priority: HIGH)

### 1.1 Split longitudinal_update.py (1281 lines → max 300 lines per file)

**Target structure:**
```
5-long/
├── longitudinal_main.py           # Main entry point and pipeline orchestration (~200 lines)
├── config_handler.py              # YAML configuration loading and validation (~150 lines)
├── data_loader.py                 # SSM and longitudinal data loading (~200 lines)
├── marker_validator.py            # Fixed marker validation and processing (~100 lines)
├── tree_updater.py               # Bayesian tree updating logic (~250 lines)
├── dynamic_analysis.py           # Dynamic marker selection workflow (~250 lines)
├── fixed_analysis.py             # Fixed marker analysis workflow (~150 lines)
├── output_manager.py             # Results saving and directory management (~150 lines)
└── utils.py                      # Shared utilities and helpers (~100 lines)
```

**Tasks:**
- [ ] Extract configuration handling into `config_handler.py`
- [ ] Move data loading functions to `data_loader.py`
- [ ] Create focused `marker_validator.py` for fixed marker validation only
- [ ] Move tree updating logic to `tree_updater.py`
- [ ] Separate dynamic and fixed analysis into dedicated modules
- [ ] Create `output_manager.py` for standardized result handling
- [ ] Consolidate shared utilities in `utils.py`
- [ ] Update imports and ensure proper module dependencies

## 2. Remove Placeholder Features (Priority: HIGH)

### 2.1 Remove Non-Functional Features
- [ ] **Remove confidence metrics calculation** - Currently placeholder/non-functional
- [ ] **Remove comparative analysis feature** - Only run one mode at a time
- [ ] **Remove "both" analysis mode** - Simplify to dynamic XOR fixed
- [ ] **Remove measurement confidence tracking** - Unnecessary complexity
- [ ] **Remove performance metrics calculations** - Focus on core functionality
- [ ] **Remove prediction VAF calculations** - Placeholder implementation

### 2.2 Clean Up Arguments and Configuration
- [ ] Remove `--analysis-mode both` option from argument parser
- [ ] Simplify YAML configuration schema (remove comparative sections)
- [ ] Remove unused configuration parameters
- [ ] Remove validation logic for "both" mode

### 2.3 Audit and Remove Dead Code
- [ ] Review all functions in longitudinal_update.py for actual usage
- [ ] Remove unused imports
- [ ] Remove commented-out code blocks
- [ ] Remove debugging print statements

## 3. Simplify Fixed Marker Selection (Priority: HIGH)

### 3.1 Core Fixed Marker Functionality
**Goal:** Use constant user-specified markers, update trees based on their VAFs over time.

**Simple workflow:**
1. User provides list of gene names
2. Validate genes exist in dataset
3. For each timepoint: extract VAFs for those genes
4. Update tree distributions using Bayesian inference
5. Save updated trees and continue to next timepoint

### 3.2 Implementation Tasks
- [ ] **Simplify marker validation** - Just check if genes exist, no fancy metrics
- [ ] **Remove optimization logic from fixed mode** - No marker selection needed
- [ ] **Streamline Bayesian updating** - Focus only on tree weight updates
- [ ] **Remove unnecessary result tracking** - Just save updated trees
- [ ] **Eliminate marker performance analysis** - Not needed for fixed mode

### 3.3 Fixed Mode Input/Output
**Input:**
```yaml
analysis_mode: "fixed"
fixed_markers:
  - "TP53_17_7577120_G>A"
  - "KRAS_12_25398284_C>A"
```

**Output:**
```
output_dir/
├── updated_trees/
│   ├── phylowgs_bootstrap_summary_updated_timepoint_0.pkl
│   ├── phylowgs_bootstrap_summary_updated_timepoint_1.pkl
│   └── ...
├── marker_data/
│   ├── fixed_markers_timepoint_0.json
│   ├── fixed_markers_timepoint_1.json
│   └── ...
└── logs/
    └── fixed_analysis.log
```

## 4. Standardize Directory Structure (Priority: MEDIUM)

### 4.1 Common Output Structure
Both dynamic and fixed modes should follow this pattern:
```
output_dir/
├── analysis_config.yaml          # Copy of input configuration
├── analysis_summary.json         # High-level results summary
├── updated_trees/                # Pickle files for each timepoint
├── marker_data/                  # Marker selection/validation results
├── plots/                        # Optional visualizations
└── logs/                         # Execution logs
```

### 4.2 Standardization Tasks
- [ ] Define common directory structure for both modes
- [ ] Standardize file naming conventions
- [ ] Create consistent JSON schemas for outputs
- [ ] Ensure both modes save trees in same format
- [ ] Standardize logging across both modes

## 5. Code Quality Improvements (Priority: MEDIUM)

### 5.1 Follow First Principles
- [ ] **Single Responsibility Principle** - Each function does one thing
- [ ] **Keep functions small** - Max 50 lines per function
- [ ] **Clear naming** - Function names describe exactly what they do
- [ ] **Minimal dependencies** - Only import what's actually used
- [ ] **No premature optimization** - Focus on correctness first

### 5.2 Documentation and Comments
- [ ] Add docstrings to all functions (following user's comment preferences)
- [ ] Explain the "why" not just the "what" in comments
- [ ] Document expected input/output formats
- [ ] Add usage examples in module docstrings

### 5.3 Error Handling
- [ ] Remove complex error handling for placeholder features
- [ ] Add simple, clear error messages for actual failure modes
- [ ] Validate inputs early and fail fast
- [ ] Log errors clearly with context

## 6. Testing and Validation (Priority: LOW)

### 6.1 Manual Testing Approach
- [ ] Create simple test configurations for both modes
- [ ] Test with minimal datasets (5-10 mutations)
- [ ] Verify output file generation
- [ ] Check that trees are updated correctly

### 6.2 Integration Testing
- [ ] Test full pipeline from YAML config to final output
- [ ] Verify SLURM script compatibility
- [ ] Test error handling with invalid inputs

## Implementation Order

### Phase 1: Remove Complexity (1-2 days)
1. Remove placeholder features and dead code
2. Simplify argument parsing and configuration
3. Remove "both" analysis mode

### Phase 2: Split Files (2-3 days)
1. Extract configuration handling
2. Split data loading functions
3. Separate dynamic and fixed analysis modules
4. Create output management module

### Phase 3: Simplify Fixed Mode (1 day)
1. Streamline fixed marker validation
2. Remove unnecessary optimization logic
3. Focus on core Bayesian updating

### Phase 4: Standardize Structure (1 day)
1. Define common output format
2. Implement consistent directory structure
3. Standardize file naming

## Success Criteria

**Fixed Mode:**
- Takes user-specified markers and timepoint data
- Updates tree distributions using Bayesian inference
- Saves updated trees for each timepoint
- No optimization or marker selection logic

**Dynamic Mode:**
- Selects optimal markers at each timepoint
- Updates trees based on selected markers
- Saves both marker selections and updated trees

**Both Modes:**
- Clean, readable code in files < 300 lines
- Consistent output directory structure
- Clear error messages and logging
- YAML configuration only (no command-line complexity)

## Notes

- **Principle:** Simple, focused functionality over feature completeness
- **Goal:** Two clean, distinct analysis modes that actually work
- **Approach:** Remove everything that isn't core functionality
- **Testing:** Manual testing with real data, not unit test complexity 