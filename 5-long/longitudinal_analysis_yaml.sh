#!/bin/bash
#
# Longitudinal cancer evolution analysis SLURM script - YAML CONFIG MODE
# Uses longitudinal_update.py with YAML configuration files for clean parameter management
#
#SBATCH --job-name=longitudinal_yaml_analysis
#SBATCH --partition=pool1
#SBATCH --cpus-per-task=1
#SBATCH --mem=16G

set -e

# --- Argument Parsing and Validation ---
if [ "$#" -lt 1 ] || [ "$#" -gt 3 ]; then
    echo "Error: Incorrect number of arguments."
    echo "Usage: sbatch $0 <config_yaml_file> [additional_flags] [slurm_log_suffix]"
    echo ""
    echo "Examples:"
    echo "  sbatch $0 configs/cruk0044_fixed_markers.yaml"
    echo "  sbatch $0 configs/cruk0044_dynamic.yaml '--debug'"
    echo "  sbatch $0 configs/cruk0044_both.yaml '--debug --no-plots' 'test_run'"
    echo ""
    echo "Configuration files should be in YAML format with all required parameters."
    echo "The code directory is now specified in the YAML config file."
    echo "See config_schema.yaml for the expected structure."
    exit 1
fi

CONFIG_FILE=$1
ADDITIONAL_FLAGS=${2:-""} # Optional additional flags like --debug, --no-plots
LOG_SUFFIX=${3:-""} # Optional suffix for log files

# Validate required input files and directories
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Configuration file '$CONFIG_FILE' not found."
    exit 1
fi

# Extract key parameters from config for validation and logging setup
# This is a simple extraction - the Python script will do full validation
PATIENT_ID=$(grep "^patient_id:" "$CONFIG_FILE" | sed 's/patient_id: *"\?\([^"]*\)"\?/\1/' | tr -d '"')
OUTPUT_BASE=$(grep "base_dir:" "$CONFIG_FILE" | sed 's/.*base_dir: *"\?\([^"]*\)"\?/\1/' | tr -d '"')
CODE_DIR=$(grep "code_dir:" "$CONFIG_FILE" | sed 's/.*code_dir: *"\?\([^"]*\)"\?/\1/' | tr -d '"')

if [ ! -d "$CODE_DIR" ]; then
    echo "Error: Code directory '$CODE_DIR' (from config) not found."
    exit 1
fi

if [ -z "$PATIENT_ID" ]; then
    echo "Error: Could not extract patient_id from config file."
    exit 1
fi

if [ -z "$OUTPUT_BASE" ]; then
    echo "Error: Could not extract output base_dir from config file."
    exit 1
fi

if [ -z "$CODE_DIR" ]; then
    echo "Error: Could not extract code_dir from config file."
    exit 1
fi

echo "--- Longitudinal YAML Analysis Script Start ---"
echo "Configuration file: $CONFIG_FILE"
echo "Patient ID: $PATIENT_ID"
echo "Code directory: $CODE_DIR (from config)"
echo "Output base directory: $OUTPUT_BASE"
echo "Additional flags: $ADDITIONAL_FLAGS"

# Load Gurobi module
echo "Loading Gurobi 11.0.2 module..."
module load gurobi1102
if [ $? -ne 0 ]; then
    echo "Error: Failed to load gurobi1102 module. Exiting."
    exit 1
fi
echo "Gurobi module loaded successfully."

# --- Setup log directory ---
# Create logs directory in the output base directory
LOG_DIR="${OUTPUT_BASE}/logs"
mkdir -p "${LOG_DIR}"

# Create log file names with optional suffix
if [ -n "$LOG_SUFFIX" ]; then
    LOG_FILE="${LOG_DIR}/longitudinal_yaml_analysis_${LOG_SUFFIX}.log"
    ERR_FILE="${LOG_DIR}/longitudinal_yaml_analysis_${LOG_SUFFIX}.err"
else
    LOG_FILE="${LOG_DIR}/longitudinal_yaml_analysis.log"
    ERR_FILE="${LOG_DIR}/longitudinal_yaml_analysis.err"
fi

# Redirect subsequent script output to log files
exec > "$LOG_FILE" 2> "$ERR_FILE"

# From this point, all output goes to the log files
echo "--- Longitudinal YAML Analysis Script Execution (output redirected) ---"
echo "Job ID: $SLURM_JOB_ID"
echo "Configuration file: $CONFIG_FILE"
echo "Patient ID: $PATIENT_ID"
echo "Code directory: $CODE_DIR"
echo "Output base directory: $OUTPUT_BASE"
echo "Additional flags: $ADDITIONAL_FLAGS"
echo "Log file: $LOG_FILE"
echo "Error file: $ERR_FILE"
echo "---------------------------------------"

# --- Environment Activation ---
echo "Activating conda environment: markers_env" 
source ~/miniconda3/bin/activate markers_env
if [ $? -ne 0 ]; then
    echo "Error: Failed to activate conda environment 'markers_env'. Exiting."
    exit 1
fi
echo "Conda environment activated."

# Verify Gurobi is accessible from Python
echo "Verifying Gurobi is accessible from Python..."
python -c "import gurobipy; print(f'Gurobi version: {gurobipy.gurobi.version()}')"
if [ $? -ne 0 ]; then
    echo "Error: Failed to import gurobipy or access Gurobi."
    exit 1
fi
echo "Gurobi verification successful."

# Verify required Python packages
echo "Verifying required Python packages..."
python -c "import pandas, numpy, matplotlib, yaml; print('Core packages: OK')"
if [ $? -ne 0 ]; then
    echo "Error: Failed to import required Python packages."
    exit 1
fi
echo "Python package verification successful."

# --- Script Execution ---
LONGITUDINAL_SCRIPT_PATH="${CODE_DIR}/5-long/longitudinal_update.py"

echo "DEBUG: Longitudinal script path: $LONGITUDINAL_SCRIPT_PATH"
echo "DEBUG: Script exists: $(ls -la "$LONGITUDINAL_SCRIPT_PATH" 2>/dev/null || echo "NOT FOUND")"

if [ ! -f "$LONGITUDINAL_SCRIPT_PATH" ]; then
    echo "Error: Longitudinal analysis Python script not found at $LONGITUDINAL_SCRIPT_PATH"
    exit 1
fi

echo "Running longitudinal analysis with YAML configuration..."
echo "Command: python $LONGITUDINAL_SCRIPT_PATH --config $CONFIG_FILE $ADDITIONAL_FLAGS"

# Execute the Python script with YAML configuration
python "$LONGITUDINAL_SCRIPT_PATH" --config "$CONFIG_FILE" $ADDITIONAL_FLAGS

SCRIPT_EXIT_CODE=$?
if [ $SCRIPT_EXIT_CODE -eq 0 ]; then
    echo "Longitudinal analysis completed successfully for patient ${PATIENT_ID}."
else
    echo "Error: Longitudinal analysis failed for patient ${PATIENT_ID} with exit code $SCRIPT_EXIT_CODE."
    exit $SCRIPT_EXIT_CODE 
fi

# --- Output Summary ---
echo "=== LONGITUDINAL YAML ANALYSIS COMPLETED ==="
echo "Patient: ${PATIENT_ID}"
echo "Configuration: ${CONFIG_FILE}"
echo "Results directory: ${OUTPUT_BASE}"
echo "Logs directory: ${LOG_DIR}"
echo ""
echo "Key output files will be in subdirectories of: ${OUTPUT_BASE}"
echo "Analysis logs: ${LOG_FILE}"
echo "Error logs: ${ERR_FILE}"
echo ""
echo "Primary SLURM job log is in the submission directory (slurm-$SLURM_JOB_ID.out)."
echo "--- Longitudinal YAML Analysis Script End ---" 