#!/bin/bash
#SBATCH --job-name=aggregation
# SLURM will use default log files (e.g., slurm-%j.out in submission dir).
#SBATCH --partition=pool1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G

set -e

# --- Argument Parsing and Validation ---
if [ "$#" -ne 2 ]; then
    echo "Error: Incorrect number of arguments."
    echo "Usage: sbatch $0 <patient_id> <bootstrap_parent_directory>"
    echo "Example: sbatch $0 CRUK0001 /path/to/data/CRUK0001/initial/"
    exit 1
fi

PATIENT_ID=$1
BOOTSTRAP_PARENT_DIR=$2 # This is the directory containing bootstrapN folders
NUM_BOOTSTRAPS=100        # Hardcoded as per previous request

if [ ! -d "$BOOTSTRAP_PARENT_DIR" ]; then
    echo "Error: Bootstrap parent directory '$BOOTSTRAP_PARENT_DIR' not found."
    exit 1
fi

echo "--- Aggregation Script Start (initial output to SLURM default log) ---"

# --- Setup Log Directory (within the bootstrap parent directory) --- 
LOG_DIR_IN_PARENT="$BOOTSTRAP_PARENT_DIR/logs"
mkdir -p "$LOG_DIR_IN_PARENT"

# Redirect subsequent script output to files in LOG_DIR_IN_PARENT/
exec > "$LOG_DIR_IN_PARENT/aggregation_execution.log" 2> "$LOG_DIR_IN_PARENT/aggregation_execution.err"

# From this point, all echo and command output goes to the files defined above.
echo "--- Aggregation Script Execution (output redirected) ---"
echo "Job ID: $SLURM_JOB_ID"
echo "Patient ID: ${PATIENT_ID}"
echo "Bootstrap Parent Directory: ${BOOTSTRAP_PARENT_DIR}"
echo "Number of Bootstraps (hardcoded): ${NUM_BOOTSTRAPS}"
echo "Aggregation results will be placed in: ${BOOTSTRAP_PARENT_DIR}/aggregation_results/"
echo "---------------------------------------"

# --- Environment Activation ---
echo "Activating conda environment: preprocess_env" # Assuming this is the correct env
source ~/miniconda3/bin/activate preprocess_env
if [ $? -ne 0 ]; then
    echo "Error: Failed to activate conda environment 'preprocess_env'. Exiting."
    exit 1
fi
echo "Conda environment activated."

# --- Script Paths and Execution ---
# Assuming process_tracerx_bootstrap.py is in a '3-aggregation' subdirectory 
# relative to where aggregation.sh is located or in a globally known path.
# For robustness, you might want to define SCRIPT_DIR as in previous versions if they are co-located.
# For simplicity now, directly calling script assuming it's in PATH or relative path is fine.
PROCESS_SCRIPT_PATH="3-aggregation/process_tracerx_bootstrap.py" 

if [ ! -f "$PROCESS_SCRIPT_PATH" ]; then
    echo "Error: Aggregation Python script not found at $PROCESS_SCRIPT_PATH. Make sure it is accessible."
    # Try to find it relative to this script's location if the fixed path fails
    SCRIPT_DIR_ABS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" # Absolute dir of this script
    ALT_PROCESS_SCRIPT_PATH="${SCRIPT_DIR_ABS%/*}/3-aggregation/process_tracerx_bootstrap.py" # Assumes aggregation.sh is in a dir one level above 3-aggregation
    if [ -f "$ALT_PROCESS_SCRIPT_PATH" ]; then 
        PROCESS_SCRIPT_PATH="$ALT_PROCESS_SCRIPT_PATH"
        echo "Found script at alternative path: $PROCESS_SCRIPT_PATH"
    else 
        SCRIPT_DIR_FALLBACK="$(dirname "$0")"
        ALT_PROCESS_SCRIPT_PATH2="${SCRIPT_DIR_FALLBACK}/../3-aggregation/process_tracerx_bootstrap.py" # If aggregation.sh is in e.g. /scripts and py is in /3-aggregation
         if [ -f "$ALT_PROCESS_SCRIPT_PATH2" ]; then
            PROCESS_SCRIPT_PATH="$ALT_PROCESS_SCRIPT_PATH2"
            echo "Found script at alternative path: $PROCESS_SCRIPT_PATH"
         else
            echo "Also tried $ALT_PROCESS_SCRIPT_PATH and $ALT_PROCESS_SCRIPT_PATH2. Exiting."
            exit 1
         fi
    fi
fi

bootstrap_list=$(seq -s ' ' 1 $NUM_BOOTSTRAPS)

echo "Running Python aggregation script: $PROCESS_SCRIPT_PATH"
python "$PROCESS_SCRIPT_PATH" "${PATIENT_ID}" \
    --bootstrap-list $bootstrap_list \
    --bootstrap-parent-dir "${BOOTSTRAP_PARENT_DIR}" # Pass the direct parent directory
    # --method phylowgs # This is the default in the python script, uncomment to override

SCRIPT_EXIT_CODE=$?
if [ $SCRIPT_EXIT_CODE -eq 0 ]; then
    echo "Aggregation completed successfully for patient ${PATIENT_ID}."
else
    echo "Error: Aggregation Python script failed for patient ${PATIENT_ID} with exit code $SCRIPT_EXIT_CODE."
    exit $SCRIPT_EXIT_CODE
fi

echo "Detailed script execution logs are in: $LOG_DIR_IN_PARENT/ (aggregation_execution.log/err)"
echo "Primary SLURM job log is in the submission directory."
echo "--- Aggregation Script End (redirected output) ---" 