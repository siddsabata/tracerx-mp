#!/bin/bash
#
# Longitudinal cancer evolution analysis SLURM script
# Uses longitudinal_update.py for iterative Bayesian tree updating
#
#SBATCH --job-name=longitudinal_analysis
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
if [ "$#" -lt 6 ] || [ "$#" -gt 10 ]; then
    echo "Error: Incorrect number of arguments."
    echo "Usage: sbatch $0 <patient_id> <aggregation_directory> <ssm_file_path> <longitudinal_data_csv> <output_directory> <code_directory> [n_markers] [read_depth] [algorithm] [additional_flags]"
    echo "Example: sbatch $0 CRUK0044 /path/to/data/CRUK0044/initial/aggregation_results /path/to/data/CRUK0044/ssm.txt /path/to/data/cruk0044_liquid.csv /path/to/data/CRUK0044/longitudinal /path/to/tracerx-mp 2 90000 struct '--debug'"
    echo "Algorithms: struct, frac"
    echo "Additional flags: '--debug', '--no-plots', '--save-intermediate', etc."
    exit 1
fi

PATIENT_ID=$1
AGGREGATION_DIR=$2
SSM_FILE=$3
LONGITUDINAL_CSV=$4
OUTPUT_DIR=$5
CODE_DIR=$6  # Now mandatory - base repository directory
N_MARKERS=${7:-2} # Default to 2 markers if not provided
READ_DEPTH=${8:-90000} # Default to 90000 if not provided
ALGORITHM=${9:-struct} # Default to struct if not provided
ADDITIONAL_FLAGS=${10:-""} # Optional additional flags

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

echo "--- Longitudinal Analysis Script Start (initial output to SLURM default log) ---"

# --- Setup log directory within output directory ---
LOG_DIR="${OUTPUT_DIR}/logs"
mkdir -p "${LOG_DIR}"

# Redirect subsequent script output to files in LOG_DIR/
exec > "$LOG_DIR/longitudinal_analysis_execution.log" 2> "$LOG_DIR/longitudinal_analysis_execution.err"

# From this point, all echo and command output goes to the files defined above.
echo "--- Longitudinal Analysis Script Execution (output redirected) ---"
echo "Job ID: $SLURM_JOB_ID"
echo "Patient ID: ${PATIENT_ID}"
echo "Aggregation Directory: ${AGGREGATION_DIR}"
echo "SSM File: ${SSM_FILE}"
echo "Longitudinal CSV: ${LONGITUDINAL_CSV}"
echo "Output Directory: ${OUTPUT_DIR}"
echo "Code Directory: ${CODE_DIR}"
echo "Number of Markers: ${N_MARKERS}"
echo "Read Depth: ${READ_DEPTH}"
echo "Algorithm: ${ALGORITHM}"
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

echo "Running longitudinal analysis Python script: $LONGITUDINAL_SCRIPT_PATH"

# Build the command with required arguments
CMD="python \"$LONGITUDINAL_SCRIPT_PATH\" \"${PATIENT_ID}\" \
    --aggregation-dir \"${AGGREGATION_DIR}\" \
    --ssm-file \"${SSM_FILE}\" \
    --longitudinal-data \"${LONGITUDINAL_CSV}\" \
    --output-dir \"${OUTPUT_DIR}\" \
    --n-markers \"${N_MARKERS}\" \
    --read-depth \"${READ_DEPTH}\" \
    --algorithm \"${ALGORITHM}\""

# Add any additional flags
if [ -n "$ADDITIONAL_FLAGS" ]; then
    CMD="$CMD $ADDITIONAL_FLAGS"
fi

echo "Executing command: $CMD"
eval $CMD

SCRIPT_EXIT_CODE=$?
if [ $SCRIPT_EXIT_CODE -eq 0 ]; then
    echo "Longitudinal analysis completed successfully for patient ${PATIENT_ID}."
else
    echo "Error: Longitudinal analysis Python script failed for patient ${PATIENT_ID} with exit code $SCRIPT_EXIT_CODE."
    exit $SCRIPT_EXIT_CODE 
fi

# --- Output Summary ---
echo "=== LONGITUDINAL ANALYSIS COMPLETED ==="
echo "Patient: ${PATIENT_ID}"
echo "Results directory: ${OUTPUT_DIR}"
echo "Logs directory: ${LOG_DIR}"
echo ""
echo "Key output files:"
echo "- Updated tree distributions: ${OUTPUT_DIR}/updated_trees/"
echo "- Marker selections per timepoint: ${OUTPUT_DIR}/marker_selections/"
echo "- Analysis logs: ${LOG_DIR}/longitudinal_analysis_execution.log"
echo ""
echo "Primary SLURM job log (initial messages) is in the submission directory (e.g., slurm-$SLURM_JOB_ID.out)."
echo "--- Longitudinal Analysis Script End (redirected output) ---" 