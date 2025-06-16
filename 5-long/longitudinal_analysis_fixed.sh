#!/bin/bash
#
# Longitudinal cancer evolution analysis SLURM script - FIXED MARKER MODE
# Uses longitudinal_update.py with user-specified fixed markers
#
#SBATCH --job-name=longitudinal_fixed_analysis
# SLURM will use default log files (e.g., slurm-%j.out in submission dir for initial output).
#SBATCH --partition=pool1
#SBATCH --cpus-per-task=1
#SBATCH --mem=16G

set -e

# load gurobi
echo "Loading Gurobi 11.0.2 module..."
module load gurobi1102
if [ $? -ne 0 ]; then
    echo "Error: Failed to load gurobi1102 module. Exiting."
    exit 1
fi
echo "Gurobi module loaded successfully."

# --- Argument Parsing and Validation ---
if [ "$#" -lt 6 ] || [ "$#" -gt 8 ]; then
    echo "Error: Incorrect number of arguments."
    echo "Usage: sbatch $0 <patient_id> <aggregation_directory> <ssm_file_path> <longitudinal_data_csv> <output_directory> <code_directory> [read_depth] [additional_flags]"
    echo "Example: sbatch $0 CRUK0044 /path/to/data/CRUK0044/initial/aggregation_results /path/to/data/CRUK0044/ssm.txt /path/to/data/cruk0044_liquid.csv /path/to/data/CRUK0044/longitudinal_fixed /path/to/tracerx-mp 90000 '--debug'"
    echo "Fixed markers used: DLG2 GPR65 C12orf74 CSMD1 OR51D1"
    echo "Additional flags: '--debug', '--no-plots', '--save-intermediate', etc."
    exit 1
fi

PATIENT_ID=$1
AGGREGATION_DIR=$2
SSM_FILE=$3
LONGITUDINAL_CSV=$4
OUTPUT_DIR=$5
CODE_DIR=$6  # Now mandatory - base repository directory
READ_DEPTH=${7:-90000} # Default to 90000 if not provided
ADDITIONAL_FLAGS=${8:-""} # Optional additional flags

# Fixed markers - these are the clinically specified genes
FIXED_MARKERS="DLG2_11_83544685_T>A GPR65_14_88477948_G>T C12orf74_12_93100715_G>T CSMD1_8_2975974_G>T OR51D1_11_4661941_G>T"

# Validate required input files and directories
if [ ! -d "$AGGREGATION_DIR" ]; then
    echo "Error: Aggregation directory '$AGGREGATION_DIR' not found."
    exit 1
fi

if [ ! -f "$SSM_FILE" ]; then
    echo "Error: SSM file '$SSM_FILE' not found."
    exit 1
fi

if [ ! -f "$LONGITUDINAL_CSV" ]; then
    echo "Error: Longitudinal CSV file '$LONGITUDINAL_CSV' not found."
    exit 1
fi

if [ ! -d "$CODE_DIR" ]; then
    echo "Error: Code directory '$CODE_DIR' not found."
    exit 1
fi

if [ ! -d "$OUTPUT_DIR" ]; then
    echo "Error: Output directory '$OUTPUT_DIR' not found. Please create it before running this script."
    exit 1
fi

echo "--- Longitudinal Fixed Marker Analysis Script Start (initial output to SLURM default log) ---"

# --- Setup log directory within output directory ---
LOG_DIR="${OUTPUT_DIR}/logs"
mkdir -p "${LOG_DIR}"

# Redirect subsequent script output to files in LOG_DIR/
exec > "$LOG_DIR/longitudinal_fixed_analysis_execution.log" 2> "$LOG_DIR/longitudinal_fixed_analysis_execution.err"

# From this point, all echo and command output goes to the files defined above.
echo "--- Longitudinal Fixed Marker Analysis Script Execution (output redirected) ---"
echo "Job ID: $SLURM_JOB_ID"
echo "Patient ID: ${PATIENT_ID}"
echo "Aggregation Directory: ${AGGREGATION_DIR}"
echo "SSM File: ${SSM_FILE}"
echo "Longitudinal CSV: ${LONGITUDINAL_CSV}"
echo "Output Directory: ${OUTPUT_DIR}"
echo "Code Directory: ${CODE_DIR}"
echo "Analysis Mode: FIXED MARKERS"
echo "Fixed Markers: ${FIXED_MARKERS}"
echo "Read Depth: ${READ_DEPTH}"
echo "Additional Flags: ${ADDITIONAL_FLAGS}"
echo "Log Directory: ${LOG_DIR}"
echo "---------------------------------------"

# --- Environment Activation ---
# Activate the same conda environment as marker selection
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
    echo "Error: Failed to import gurobipy or access Gurobi. Check that the module is properly loaded and gurobipy is installed."
    exit 1
fi
echo "Gurobi verification successful."

# Verify required Python packages are available
echo "Verifying required Python packages..."
python -c "import pandas, numpy, matplotlib; print('Core packages: OK')"
if [ $? -ne 0 ]; then
    echo "Error: Failed to import required Python packages (pandas, numpy, matplotlib)."
    exit 1
fi
echo "Python package verification successful."

# --- Script Paths and Execution ---
# Use the absolute path to the longitudinal_update.py script based on the provided code directory
LONGITUDINAL_SCRIPT_PATH="${CODE_DIR}/5-long/longitudinal_update.py"

# Debug: Print the actual script path being used
echo "DEBUG: Longitudinal script path: $LONGITUDINAL_SCRIPT_PATH"
echo "DEBUG: Script exists check: $(ls -la "$LONGITUDINAL_SCRIPT_PATH" 2>/dev/null || echo "NOT FOUND")"

if [ ! -f "$LONGITUDINAL_SCRIPT_PATH" ]; then
    echo "Error: Longitudinal analysis Python script not found at $LONGITUDINAL_SCRIPT_PATH. Exiting."
    exit 1
fi

echo "Running longitudinal fixed marker analysis Python script: $LONGITUDINAL_SCRIPT_PATH"

# Build the command with required arguments for FIXED MARKER MODE
CMD="python \"$LONGITUDINAL_SCRIPT_PATH\" \"${PATIENT_ID}\" \
    --aggregation-dir \"${AGGREGATION_DIR}\" \
    --ssm-file \"${SSM_FILE}\" \
    --longitudinal-data \"${LONGITUDINAL_CSV}\" \
    --output-dir \"${OUTPUT_DIR}\" \
    --analysis-mode fixed \
    --fixed-markers ${FIXED_MARKERS} \
    --read-depth \"${READ_DEPTH}\""

# Add any additional flags
if [ -n "$ADDITIONAL_FLAGS" ]; then
    CMD="$CMD $ADDITIONAL_FLAGS"
fi

echo "Executing command: $CMD"
echo "Fixed markers being tracked: ${FIXED_MARKERS}"
echo "Analysis mode: FIXED (user-specified markers)"
eval $CMD

SCRIPT_EXIT_CODE=$?
if [ $SCRIPT_EXIT_CODE -eq 0 ]; then
    echo "Longitudinal fixed marker analysis completed successfully for patient ${PATIENT_ID}."
else
    echo "Error: Longitudinal fixed marker analysis Python script failed for patient ${PATIENT_ID} with exit code $SCRIPT_EXIT_CODE."
    exit $SCRIPT_EXIT_CODE 
fi

# --- Output Summary ---
echo "=== LONGITUDINAL FIXED MARKER ANALYSIS COMPLETED ==="
echo "Patient: ${PATIENT_ID}"
echo "Analysis Mode: FIXED MARKERS"
echo "Fixed Markers Tracked: ${FIXED_MARKERS}"
echo "Results directory: ${OUTPUT_DIR}"
echo "Logs directory: ${LOG_DIR}"
echo ""
echo "Key output files:"
echo "- Fixed marker analysis results: ${OUTPUT_DIR}/fixed_marker_analysis/"
echo "- Updated tree distributions: ${OUTPUT_DIR}/fixed_marker_analysis/updated_trees/"
echo "- Marker tracking results: ${OUTPUT_DIR}/fixed_marker_analysis/marker_tracking/"
echo "- Complete results: ${OUTPUT_DIR}/fixed_marker_analysis/fixed_marker_complete_results.json"
echo "- Analysis logs: ${LOG_DIR}/longitudinal_fixed_analysis_execution.log"
echo ""
echo "Primary SLURM job log (initial messages) is in the submission directory (e.g., slurm-$SLURM_JOB_ID.out)."
echo "--- Longitudinal Fixed Marker Analysis Script End (redirected output) ---" 