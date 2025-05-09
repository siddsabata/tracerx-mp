#!/bin/bash
#SBATCH --job-name=bootstrap_only
# SLURM will use default log files (e.g., slurm-%j.out in submission dir).
#SBATCH --partition=pool1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G

# Usage: sbatch bootstrap.sh <input_ssm_file> <output_directory> [num_bootstraps]

# --- Argument Parsing --- 
if [ "$#" -lt 2 ] || [ "$#" -gt 3 ]; then
    echo "Error: Incorrect number of arguments."
    echo "Usage: sbatch $0 <input_ssm_file> <output_directory> [num_bootstraps (default: 100)]"
    exit 1
fi

INPUT_SSM_FILE=$1
OUTPUT_BASE_DIR=$2
NUM_BOOTSTRAPS=${3:-100} # Default to 100 if not provided

echo "--- Bootstrap Script Start (initial output to SLURM default log) ---"

# --- Setup Log and Output Directories --- 
mkdir -p "$OUTPUT_BASE_DIR/logs"

# Redirect subsequent script output to files in $OUTPUT_BASE_DIR/logs/
# These will be overwritten if the script is run multiple times with the same OUTPUT_BASE_DIR.
exec > "$OUTPUT_BASE_DIR/logs/bootstrap_execution.log" 2> "$OUTPUT_BASE_DIR/logs/bootstrap_execution.err"

# From this point, all echo and command output goes to the files defined above.
echo "--- Bootstrap Script Execution (output redirected) ---"
echo "Input SSM File: $INPUT_SSM_FILE"
echo "Output Base Directory: $OUTPUT_BASE_DIR"
echo "Number of Bootstraps: $NUM_BOOTSTRAPS"

# --- Environment Activation ---
echo "Activating conda environment: preprocess_env"
source ~/miniconda3/bin/activate preprocess_env
if [ $? -ne 0 ]; then
    echo "Error: Failed to activate conda environment 'preprocess_env'. Exiting."
    exit 1
fi
echo "Conda environment preprocess_env activated successfully."

# --- Run Bootstrap Script ---
echo "Running 1-bootstrap/bootstrap.py..."
python3 1-bootstrap/bootstrap.py \
    -i "$INPUT_SSM_FILE" \
    -o "$OUTPUT_BASE_DIR" \
    -n "$NUM_BOOTSTRAPS"

SCRIPT_EXIT_CODE=$?
if [ $SCRIPT_EXIT_CODE -eq 0 ]; then
    echo "1-bootstrap/bootstrap.py completed successfully."
else
    echo "Error: 1-bootstrap/bootstrap.py script failed with exit code $SCRIPT_EXIT_CODE."
    exit $SCRIPT_EXIT_CODE
fi

echo "Bootstrapped files should be in subdirectories within: $OUTPUT_BASE_DIR"
echo "Detailed script execution logs are in: $OUTPUT_BASE_DIR/logs/ (bootstrap_execution.log/err)"
echo "Primary SLURM job log is in the submission directory."
echo "--- Bootstrap Script End (redirected output) ---" 