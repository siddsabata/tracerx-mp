#!/bin/bash
#SBATCH --job-name=bootstrap_only
# SLURM will use default log files (e.g., slurm-%j.out in submission dir).
#SBATCH --partition=pool1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G

# Usage: sbatch bootstrap.sh <input_ssm_file> <output_directory> <code_directory> [num_bootstraps]

# --- Argument Parsing --- 
if [ "$#" -lt 3 ] || [ "$#" -gt 4 ]; then
    echo "Error: Incorrect number of arguments."
    echo "Usage: sbatch $0 <input_ssm_file> <output_directory> <code_directory> [num_bootstraps (default: 100)]"
    exit 1
fi

INPUT_SSM_FILE=$1
OUTPUT_BASE_DIR=$2
CODE_DIR=$3
NUM_BOOTSTRAPS=${4:-100} # Default to 100 if not provided

echo "--- Bootstrap Script Start (initial output to SLURM default log) ---"

# --- Setup Log and Output Directories --- 
mkdir -p "$OUTPUT_BASE_DIR/logs"

# Define the actual directory where bootstrapN folders will be created
BOOTSTRAP_DATA_DIR="$OUTPUT_BASE_DIR/bootstraps"
mkdir -p "$BOOTSTRAP_DATA_DIR"

# Redirect subsequent script output to files in $OUTPUT_BASE_DIR/logs/
# These will be overwritten if the script is run multiple times with the same OUTPUT_BASE_DIR.
exec > "$OUTPUT_BASE_DIR/logs/bootstrap_execution.log" 2> "$OUTPUT_BASE_DIR/logs/bootstrap_execution.err"

# From this point, all echo and command output goes to the files defined above.
echo "--- Bootstrap Script Execution (output redirected) ---"
echo "Input SSM File: $INPUT_SSM_FILE"
echo "Output Base Directory: $OUTPUT_BASE_DIR"
echo "Code Directory: $CODE_DIR"
echo "Number of Bootstraps: $NUM_BOOTSTRAPS"

# Verify the input file exists
if [ ! -f "$INPUT_SSM_FILE" ]; then
    echo "Error: Input SSM file not found at $INPUT_SSM_FILE"
    exit 1
fi

# --- Environment Activation ---
echo "Activating conda environment: preprocess_env"
source ~/miniconda3/bin/activate preprocess_env
if [ $? -ne 0 ]; then
    echo "Error: Failed to activate conda environment 'preprocess_env'. Exiting."
    exit 1
fi
echo "Conda environment preprocess_env activated successfully."

# --- Run Bootstrap Script ---
echo "Running step1_bootstrap.py..."

# Use the absolute path to the step1_bootstrap.py file based on the provided code directory
BOOTSTRAP_PY_PATH="${CODE_DIR}/src/bootstrap/step1_bootstrap.py"
echo "Using step1_bootstrap.py at: $BOOTSTRAP_PY_PATH"

# Verify the step1_bootstrap.py file exists
if [ ! -f "$BOOTSTRAP_PY_PATH" ]; then
    echo "Error: Could not find step1_bootstrap.py at $BOOTSTRAP_PY_PATH"
    echo "Current working directory: $(pwd)"
    echo "Files in code directory: $(ls -la $CODE_DIR/src/bootstrap/)"
    exit 1
fi

python3 "$BOOTSTRAP_PY_PATH" \
    -i "$INPUT_SSM_FILE" \
    -o "$BOOTSTRAP_DATA_DIR" \
    -n "$NUM_BOOTSTRAPS"

SCRIPT_EXIT_CODE=$?
if [ $SCRIPT_EXIT_CODE -eq 0 ]; then
    echo "step1_bootstrap.py completed successfully."
else
    echo "Error: step1_bootstrap.py script failed with exit code $SCRIPT_EXIT_CODE."
    exit $SCRIPT_EXIT_CODE
fi

echo "Bootstrapped files should be in subdirectories within: $BOOTSTRAP_DATA_DIR"
echo "Detailed script execution logs are in: $OUTPUT_BASE_DIR/logs/ (bootstrap_execution.log/err)"
echo "Primary SLURM job log is in the submission directory."
echo "--- Bootstrap Script End (redirected output) ---" 