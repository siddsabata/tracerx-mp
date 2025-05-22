#!/bin/bash
#SBATCH --job-name=aggregation
# SLURM will use default log files (e.g., slurm-%j.out in submission dir).
#SBATCH --partition=pool1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G

set -e

# --- Argument Parsing and Validation ---
if [ "$#" -ne 3 ]; then
    echo "Error: Incorrect number of arguments."
    echo "Usage: sbatch $0 <patient_id> <bootstrap_parent_directory> <code_directory>"
    echo "Example: sbatch $0 CRUK0001 /path/to/data/initial/bootstraps /path/to/tracerx-mp"
    exit 1
fi

PATIENT_ID=$1
BOOTSTRAP_PARENT_DIR=$2 # This is the directory containing bootstrapN folders
CODE_DIR=$3
NUM_BOOTSTRAPS=100        # Hardcoded as per previous request

if [ ! -d "$BOOTSTRAP_PARENT_DIR" ]; then
    echo "Error: Bootstrap parent directory '$BOOTSTRAP_PARENT_DIR' not found."
    exit 1
fi

if [ ! -d "$CODE_DIR" ]; then
    echo "Error: Code directory '$CODE_DIR' not found."
    exit 1
fi

echo "--- Aggregation Script Start (initial output to SLURM default log) ---"

# --- Setup Log Directory (in the parent of BOOTSTRAP_PARENT_DIR) --- 
# BOOTSTRAP_PARENT_DIR is now expected to be the directory containing bootstrapN folders (e.g., .../initial/bootstraps)
LOG_DIR_IN_PARENT="$(dirname "$BOOTSTRAP_PARENT_DIR")/logs"
mkdir -p "$LOG_DIR_IN_PARENT"

# Redirect subsequent script output to files in LOG_DIR_IN_PARENT/
exec > "$LOG_DIR_IN_PARENT/aggregation_execution.log" 2> "$LOG_DIR_IN_PARENT/aggregation_execution.err"

# From this point, all echo and command output goes to the files defined above.
echo "--- Aggregation Script Execution (output redirected) ---"
echo "Job ID: $SLURM_JOB_ID"
echo "Patient ID: ${PATIENT_ID}"
echo "Bootstrap Parent Directory: ${BOOTSTRAP_PARENT_DIR}"
echo "Code Directory: ${CODE_DIR}"
echo "Number of Bootstraps (hardcoded): ${NUM_BOOTSTRAPS}"
echo "Aggregation results will be placed in: ${BOOTSTRAP_PARENT_DIR}/aggregation_results/"
echo "---------------------------------------"

# --- Environment Activation ---
echo "Activating conda environment: aggregation_env" # Changed from preprocess_env
source ~/miniconda3/bin/activate aggregation_env # Changed from preprocess_env
if [ $? -ne 0 ]; then
    echo "Error: Failed to activate conda environment 'aggregation_env'. Exiting."
    exit 1
fi
echo "Conda environment activated."

# --- Script Paths and Execution ---
# Use the absolute path to the aggregation.py script based on the provided code directory
PROCESS_SCRIPT_PATH="${CODE_DIR}/3-aggregation/aggregate.py"

if [ ! -f "$PROCESS_SCRIPT_PATH" ]; then
    echo "Error: Aggregation Python script not found at $PROCESS_SCRIPT_PATH. Exiting."
    exit 1
fi

bootstrap_list=$(seq -s ' ' 1 $NUM_BOOTSTRAPS)

# BOOTSTRAP_PARENT_DIR argument is now the direct path to bootstrapN folders.
# Define the target output directory for final aggregation results (in the parent of BOOTSTRAP_PARENT_DIR)
FINAL_AGGREGATION_OUTPUT_DIR="$(dirname "$BOOTSTRAP_PARENT_DIR")/aggregation_results"
mkdir -p "${FINAL_AGGREGATION_OUTPUT_DIR}"

# Path where the Python script might write its output if relative to its input dir
TEMP_PYTHON_OUTPUT_DIR="${BOOTSTRAP_PARENT_DIR}/aggregation_results"

echo "Running Python aggregation script: $PROCESS_SCRIPT_PATH"
echo "Input bootstrap data expected from: $BOOTSTRAP_PARENT_DIR"
echo "Final aggregation output will be in: $FINAL_AGGREGATION_OUTPUT_DIR"

python "$PROCESS_SCRIPT_PATH" "${PATIENT_ID}" \
    --bootstrap-list $bootstrap_list \
    --bootstrap-parent-dir "${BOOTSTRAP_PARENT_DIR}" # Pass the directory containing bootstrapN folders directly
    # --method phylowgs # This is the default in the python script, uncomment to override

SCRIPT_EXIT_CODE=$?
if [ $SCRIPT_EXIT_CODE -eq 0 ]; then
    echo "Aggregation Python script completed successfully for patient ${PATIENT_ID}."
    
    # Move results if the python script created output within its input bootstrap data directory
    if [ -d "${TEMP_PYTHON_OUTPUT_DIR}" ]; then
        echo "Moving aggregation results from ${TEMP_PYTHON_OUTPUT_DIR} to ${FINAL_AGGREGATION_OUTPUT_DIR}"
        mkdir -p "${FINAL_AGGREGATION_OUTPUT_DIR}" # Ensure target exists
        # Move contents. Using cp and rm for simplicity.
        cp -r "${TEMP_PYTHON_OUTPUT_DIR}/"* "${FINAL_AGGREGATION_OUTPUT_DIR}/"
        if [ $? -eq 0 ]; then
            echo "Successfully copied results. Removing temporary output directory: ${TEMP_PYTHON_OUTPUT_DIR}"
            rm -rf "${TEMP_PYTHON_OUTPUT_DIR}"
        else
            echo "Error: Failed to copy results from ${TEMP_PYTHON_OUTPUT_DIR} to ${FINAL_AGGREGATION_OUTPUT_DIR}."
            echo "Manual check required. Temporary files left at ${TEMP_PYTHON_OUTPUT_DIR}"
        fi
    else
        echo "Note: Assumed Python output directory ${TEMP_PYTHON_OUTPUT_DIR} not found. Assuming Python script wrote directly to a pre-configured location or had its own output path logic."
        echo "Please verify aggregation results are in ${FINAL_AGGREGATION_OUTPUT_DIR}"
    fi
else
    echo "Error: Aggregation Python script failed for patient ${PATIENT_ID} with exit code $SCRIPT_EXIT_CODE."
    exit $SCRIPT_EXIT_CODE
fi

echo "Detailed script execution logs are in: $LOG_DIR_IN_PARENT/ (aggregation_execution.log/err)"
echo "Primary SLURM job log is in the submission directory."
echo "--- Aggregation Script End (redirected output) ---" 