#!/bin/bash
#SBATCH --job-name=marker_selection
# SLURM will use default log files (e.g., slurm-%j.out in submission dir for initial output).
#SBATCH --partition=pool1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G

set -e

# --- Argument Parsing and Validation ---
if [ "$#" -lt 4 ] || [ "$#" -gt 5 ]; then
    echo "Error: Incorrect number of arguments."
    echo "Usage: sbatch $0 <patient_id> <aggregation_directory> <ssm_file_path> <code_directory> [read_depth]"
    echo "Example: sbatch $0 CRUK0001 /path/to/data/CRUK0001/initial/aggregation_results /path/to/data/CRUK0001/ssm.txt /path/to/tracerx-mp 1500"
    exit 1
fi

PATIENT_ID=$1
AGGREGATION_DIR=$2
SSM_FILE=$3
CODE_DIR=$4
READ_DEPTH=${5:-1500} # Default to 1500 if not provided

# Convert relative paths to absolute paths if needed
if [[ ! "$AGGREGATION_DIR" = /* ]]; then
    # If the path doesn't start with /, it's a relative path
    AGGREGATION_DIR="$(pwd)/$AGGREGATION_DIR"
    echo "Converted aggregation directory path to absolute: $AGGREGATION_DIR"
fi

if [[ ! "$SSM_FILE" = /* ]]; then
    # If the path doesn't start with /, it's a relative path
    SSM_FILE="$(pwd)/$SSM_FILE"
    echo "Converted SSM file path to absolute: $SSM_FILE"
fi

if [[ ! "$CODE_DIR" = /* ]]; then
    # If the path doesn't start with /, it's a relative path
    CODE_DIR="$(pwd)/$CODE_DIR"
    echo "Converted code directory path to absolute: $CODE_DIR"
fi

if [ ! -d "$AGGREGATION_DIR" ]; then
    echo "Error: Aggregation directory '$AGGREGATION_DIR' not found."
    exit 1
fi

if [ ! -f "$SSM_FILE" ]; then
    echo "Error: SSM file '$SSM_FILE' not found."
    exit 1
fi

if [ ! -d "$CODE_DIR" ]; then
    echo "Error: Code directory '$CODE_DIR' not found."
    exit 1
fi

echo "--- Marker Selection Script Start (initial output to SLURM default log) ---"

# --- Setup directories and paths ---
# Get the parent directory of the aggregation directory (should be the 'initial' directory)
INITIAL_DIR="$(dirname "$AGGREGATION_DIR")"
MARKERS_DIR="${INITIAL_DIR}/markers"
LOG_DIR="${INITIAL_DIR}/logs"

# Create the markers directory if it doesn't exist
mkdir -p "${MARKERS_DIR}"
mkdir -p "${LOG_DIR}"

# Redirect subsequent script output to files in LOG_DIR/
exec > "$LOG_DIR/marker_selection_execution.log" 2> "$LOG_DIR/marker_selection_execution.err"

# From this point, all echo and command output goes to the files defined above.
echo "--- Marker Selection Script Execution (output redirected) ---"
echo "Job ID: $SLURM_JOB_ID"
echo "Patient ID: ${PATIENT_ID}"
echo "Aggregation Directory: ${AGGREGATION_DIR}"
echo "Markers Directory: ${MARKERS_DIR}"
echo "SSM File: ${SSM_FILE}"
echo "Code Directory: ${CODE_DIR}"
echo "Read Depth: ${READ_DEPTH}"
echo "Log Directory: ${LOG_DIR}"
echo "---------------------------------------"

# --- Environment Activation ---
# Assuming the same environment as aggregation.sh, or a suitable one for run_data.py
echo "Activating conda environment: markers_env" 
source ~/miniconda3/bin/activate markers_env
if [ $? -ne 0 ]; then
    echo "Error: Failed to activate conda environment 'markers_env'. Exiting."
    exit 1
fi
echo "Conda environment activated."

# --- Script Paths and Execution ---
# Use the absolute path to the run_data.py script based on the provided code directory
MARKER_SCRIPT_PATH="${CODE_DIR}/4-markers/run_data.py"

if [ ! -f "$MARKER_SCRIPT_PATH" ]; then
    echo "Error: Marker selection Python script not found at $MARKER_SCRIPT_PATH. Exiting."
    exit 1
fi

echo "Running Python marker selection script: $MARKER_SCRIPT_PATH"
python "$MARKER_SCRIPT_PATH" "${PATIENT_ID}" \
    --aggregation-dir "${AGGREGATION_DIR}" \
    --ssm-file "${SSM_FILE}" \
    --read-depth "${READ_DEPTH}" \
    --output-dir "${MARKERS_DIR}"

SCRIPT_EXIT_CODE=$?
if [ $SCRIPT_EXIT_CODE -eq 0 ]; then
    echo "Marker selection completed successfully for patient ${PATIENT_ID}."
else
    echo "Error: Marker selection Python script failed for patient ${PATIENT_ID} with exit code $SCRIPT_EXIT_CODE."
    # Consider exiting the sbatch script with the Python script's error code
    exit $SCRIPT_EXIT_CODE 
fi

echo "Detailed Python script output is in: ${MARKERS_DIR}"
echo "Script execution logs are in: ${LOG_DIR} (marker_selection_execution.log/err)"
echo "Primary SLURM job log (initial messages) is in the submission directory (e.g., slurm-$SLURM_JOB_ID.out)."
echo "--- Marker Selection Script End (redirected output) ---" 