#!/bin/bash
#SBATCH --job-name=phylowgs
#SBATCH --partition=pool1
#SBATCH --cpus-per-task=5
#SBATCH --mem=8G
#SBATCH --array=0-99%10
# IMPORTANT: User must submit this script with a SLURM --array directive.
# Example: sbatch --array=0-19%10 phylowgs.sh /path/to/bootstrap_base_dir

# Usage: sbatch --array=<range> phylowgs.sh <base_directory_containing_bootstrap_folders>

if [ "$#" -ne 1 ]; then
    echo "Error: Base directory must be provided."
    echo "Usage: sbatch --array=<range> $0 <base_directory_containing_bootstrap_folders>"
    exit 1
fi

if [ -z "$SLURM_ARRAY_TASK_ID" ]; then
    echo "Error: This script must be run as a SLURM job array. SLURM_ARRAY_TASK_ID is not set."
    echo "Please submit with a --array option, e.g., sbatch --array=0-19%10 $0 <base_dir>"
    exit 1
fi

BASE_DIR=$1

if [ ! -d "$BASE_DIR" ]; then
    echo "Error: Base directory '$BASE_DIR' not found." >&2 # Send error to stderr
    exit 1
fi

# activate phylowgs environment
source ~/miniconda3/bin/activate phylowgs_env

phylowgs_dir="$(pwd)/2-phylowgs/phylowgs" # Assumes script is run from project root
multievolve="${phylowgs_dir}/multievolve.py"
write_results="${phylowgs_dir}/write_results.py"

# List all bootstrap directories and select the one for this task ID
# Note: This assumes bootstrap directories are numerically named (bootstrap1, bootstrap2, etc.)
# and that the array task ID will correspond to these if sorted numerically.
# A more robust way would be to ensure a specific naming or pass the exact dir name.
# For simplicity and matching original structure, we rely on ls and array indexing.
BOOTSTRAP_DIRS=($(ls -vd ${BASE_DIR}/bootstrap* 2>/dev/null))

if [ "$SLURM_ARRAY_TASK_ID" -ge "${#BOOTSTRAP_DIRS[@]}" ]; then
    echo "Error: SLURM_ARRAY_TASK_ID $SLURM_ARRAY_TASK_ID is out of bounds for the number of bootstrap directories found (${#BOOTSTRAP_DIRS[@]})." >&2
    exit 1
fi

CURRENT_BOOTSTRAP_DIR_PATH="${BOOTSTRAP_DIRS[$SLURM_ARRAY_TASK_ID]}"
BOOTSTRAP_DIR_NAME=$(basename "$CURRENT_BOOTSTRAP_DIR_PATH")
BOOTSTRAP_NUM=$(echo "$BOOTSTRAP_DIR_NAME" | sed 's/bootstrap//') # Extracts N from bootstrapN

# Create bootstrap-specific log directory and redirect output
mkdir -p "${CURRENT_BOOTSTRAP_DIR_PATH}/logs"
exec > "${CURRENT_BOOTSTRAP_DIR_PATH}/logs/phylowgs_${BOOTSTRAP_DIR_NAME}.log" 2> "${CURRENT_BOOTSTRAP_DIR_PATH}/logs/phylowgs_${BOOTSTRAP_DIR_NAME}.err"

echo "--- PhyloWGS Processing for Bootstrap Sample: $BOOTSTRAP_DIR_NAME ---"
echo "Job ID: $SLURM_JOB_ID, Array Task ID: $SLURM_ARRAY_TASK_ID"
echo "Directory: $CURRENT_BOOTSTRAP_DIR_PATH"
echo "Bootstrap Number: $BOOTSTRAP_NUM"

SSM_FILE="${CURRENT_BOOTSTRAP_DIR_PATH}/ssm_data_bootstrap${BOOTSTRAP_NUM}.txt"
CNV_FILE="${CURRENT_BOOTSTRAP_DIR_PATH}/cnv_data_bootstrap${BOOTSTRAP_NUM}.txt"
CHAINS_DIR="${CURRENT_BOOTSTRAP_DIR_PATH}/chains"

if [ ! -f "$SSM_FILE" ]; then
    echo "Error: SSM file $SSM_FILE not found!" >&2
    exit 1
fi
if [ ! -f "$CNV_FILE" ]; then
    echo "Error: CNV file $CNV_FILE not found! PhyloWGS expects this, even if empty." >&2
    exit 1
fi

mkdir -p "$CHAINS_DIR"

echo "Running multievolve.py for $BOOTSTRAP_DIR_NAME..."
python2 "${multievolve}" --num-chains 5 \
        --ssms "$SSM_FILE" \
        --cnvs "$CNV_FILE" \
        --output-dir "$CHAINS_DIR"

PY2_MULTI_EXIT_CODE=$?
if [ $PY2_MULTI_EXIT_CODE -ne 0 ]; then
    echo "Error: multievolve.py failed for $BOOTSTRAP_DIR_NAME with exit code $PY2_MULTI_EXIT_CODE." >&2
    exit $PY2_MULTI_EXIT_CODE
fi

echo "Running write_results.py for $BOOTSTRAP_DIR_NAME..."
python2 "${write_results}" --include-ssm-names result \
                "${CHAINS_DIR}/trees.zip" \
                "${CURRENT_BOOTSTRAP_DIR_PATH}/result.summ.json.gz" \
                "${CURRENT_BOOTSTRAP_DIR_PATH}/result.muts.json.gz" \
                "${CURRENT_BOOTSTRAP_DIR_PATH}/result.mutass.zip"

PY2_WRITE_EXIT_CODE=$?
if [ $PY2_WRITE_EXIT_CODE -ne 0 ]; then
    echo "Error: write_results.py failed for $BOOTSTRAP_DIR_NAME with exit code $PY2_WRITE_EXIT_CODE." >&2
    exit $PY2_WRITE_EXIT_CODE
fi

echo "--- Completed PhyloWGS for Bootstrap Sample: $BOOTSTRAP_DIR_NAME ---"