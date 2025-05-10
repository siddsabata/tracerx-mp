#!/bin/bash
#SBATCH --job-name=marker_selection
# SLURM will use default log files (e.g., slurm-%j.out in submission dir for initial output).
#SBATCH --partition=pool1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G

set -e

# --- Argument Parsing and Validation ---
if [ "$#" -lt 3 ] || [ "$#" -gt 4 ]; then
    echo "Error: Incorrect number of arguments."
    echo "Usage: sbatch $0 <patient_id> <aggregation_directory> <ssm_file_path> [read_depth]"
    echo "Example: sbatch $0 CRUK0001 /path/to/data/CRUK0001/initial/aggregation_results /path/to/data/CRUK0001/ssm.txt 1500"
    exit 1
fi

PATIENT_ID=$1
AGGREGATION_DIR=$2
SSM_FILE=$3
READ_DEPTH=${4:-1500} # Default to 1500 if not provided

if [ ! -d "$AGGREGATION_DIR" ]; then
    echo "Error: Aggregation directory '$AGGREGATION_DIR' not found."
    exit 1
fi

if [ ! -f "$SSM_FILE" ]; then
    echo "Error: SSM file '$SSM_FILE' not found."
    exit 1
fi

echo "--- Marker Selection Script Start (initial output to SLURM default log) ---"

# --- Setup Log Directory (within the aggregation directory's parent) --- 
# This is for the SLURM script's own execution logs, not the Python script's output.
# Adjusted to use the same log directory as aggregation.sh
SLURM_LOG_DIR="$(dirname "$AGGREGATION_DIR")/logs" # Changed from "$AGGREGATION_DIR/logs"
mkdir -p "$SLURM_LOG_DIR"

# Redirect subsequent script output to files in SLURM_LOG_DIR/
exec > "$SLURM_LOG_DIR/marker_selection_execution.log" 2> "$SLURM_LOG_DIR/marker_selection_execution.err"

# From this point, all echo and command output goes to the files defined above.
echo "--- Marker Selection Script Execution (output redirected) ---"
echo "Job ID: $SLURM_JOB_ID"
echo "Patient ID: ${PATIENT_ID}"
echo "Aggregation Directory: ${AGGREGATION_DIR}"
echo "SSM File: ${SSM_FILE}"
echo "Read Depth: ${READ_DEPTH}"
echo "Python script output will be placed in: ${AGGREGATION_DIR}/marker_selection_output/"
echo "SLURM script execution logs are in: ${SLURM_LOG_DIR}/"
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
# Get the directory where this script is located
SCRIPT_DIR_ABS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MARKER_SCRIPT_PATH="${SCRIPT_DIR_ABS}/run_data.py"

if [ ! -f "$MARKER_SCRIPT_PATH" ]; then
    echo "Error: Marker selection Python script not found at $MARKER_SCRIPT_PATH. Exiting."
    exit 1
fi

echo "Running Python marker selection script: $MARKER_SCRIPT_PATH"
python "$MARKER_SCRIPT_PATH" "${PATIENT_ID}" \
    --aggregation-dir "${AGGREGATION_DIR}" \
    --ssm-file "${SSM_FILE}" \
    --read-depth "${READ_DEPTH}"

SCRIPT_EXIT_CODE=$?
if [ $SCRIPT_EXIT_CODE -eq 0 ]; then
    echo "Marker selection completed successfully for patient ${PATIENT_ID}."
else
    echo "Error: Marker selection Python script failed for patient ${PATIENT_ID} with exit code $SCRIPT_EXIT_CODE."
    # Consider exiting the sbatch script with the Python script's error code
    exit $SCRIPT_EXIT_CODE 
fi

echo "Detailed Python script output is in: $AGGREGATION_DIR/marker_selection_output/"
echo "SLURM script execution logs are in: $SLURM_LOG_DIR/ (marker_selection_execution.log/err)"
echo "Primary SLURM job log (initial messages) is in the submission directory (e.g., slurm-$SLURM_JOB_ID.out)."
echo "--- Marker Selection Script End (redirected output) ---" 