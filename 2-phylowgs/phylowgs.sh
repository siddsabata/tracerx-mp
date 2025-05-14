#!/bin/bash
#SBATCH --job-name=phylowgs
#SBATCH --partition=pool1
#SBATCH --cpus-per-task=5
#SBATCH --mem=8G
#SBATCH --array=0-99%10 # Processing 100 bootstrap samples (0-99), 10 concurrently

# Usage: sbatch phylowgs.sh <base_directory_containing_bootstrap_folders> <code_directory>

if [ "$#" -ne 2 ]; then
    echo "Error: Incorrect number of arguments."
    echo "Usage: sbatch $0 <base_directory_containing_bootstrap_folders> <code_directory>"
    exit 1
fi

BASE_DIR=$1
CODE_DIR=$2

# Ensure we have absolute paths
if [[ ! "$BASE_DIR" = /* ]]; then
    echo "Error: Base directory must be an absolute path." >&2
    exit 1
fi

if [[ ! "$CODE_DIR" = /* ]]; then
    echo "Error: Code directory must be an absolute path." >&2
    exit 1
fi

if [ ! -d "$BASE_DIR" ]; then
    echo "Error: Base directory '$BASE_DIR' not found." >&2
    exit 1
fi

if [ ! -d "$CODE_DIR" ]; then
    echo "Error: Code directory '$CODE_DIR' not found." >&2
    exit 1
fi

# Print current working directory for debugging
echo "Current working directory at start: $(pwd)" >&2

# activate phylowgs environment
source ~/miniconda3/bin/activate phylowgs_env

# Use the absolute path to the phylowgs directory based on the provided code directory
phylowgs_dir="${CODE_DIR}/2-phylowgs/phylowgs"

# Check if phylowgs directory exists
if [ ! -d "$phylowgs_dir" ]; then
    echo "Error: PhyloWGS directory not found at $phylowgs_dir." >&2
    echo "Make sure to run install_phylowgs.sh first to set up the required software." >&2
    exit 1
fi

multievolve="${phylowgs_dir}/multievolve.py"
write_results="${phylowgs_dir}/write_results.py"

# List all bootstrap directories (sorted naturally)
BOOTSTRAP_DIRS=($(ls -vd ${BASE_DIR}/bootstrap* 2>/dev/null))

# Check if the SLURM_ARRAY_TASK_ID is valid for the found directories
if [ "$SLURM_ARRAY_TASK_ID" -ge "${#BOOTSTRAP_DIRS[@]}" ]; then
    echo "Error: SLURM_ARRAY_TASK_ID $SLURM_ARRAY_TASK_ID is out of bounds. Found ${#BOOTSTRAP_DIRS[@]} bootstrap directories in $BASE_DIR." >&2
    echo "Ensure there are at least $(($SLURM_ARRAY_TASK_ID + 1)) bootstrap directories (e.g., bootstrap1, bootstrap2, ..., bootstrap$(($SLURM_ARRAY_TASK_ID + 1)))" >&2
    exit 1
fi

CURRENT_BOOTSTRAP_DIR_PATH="${BOOTSTRAP_DIRS[$SLURM_ARRAY_TASK_ID]}"
BOOTSTRAP_DIR_NAME=$(basename "$CURRENT_BOOTSTRAP_DIR_PATH")
BOOTSTRAP_NUM=$(echo "$BOOTSTRAP_DIR_NAME" | sed 's/bootstrap//') # Extracts N from bootstrapN

# Find the base logs directory (one level up from bootstraps directory)
PATIENT_BASE_DIR=$(dirname "$BASE_DIR")
LOGS_DIR="${PATIENT_BASE_DIR}/logs"
PHYLOWGS_LOGS_DIR="${LOGS_DIR}/phylowgs"

# Create bootstrap-specific log directory with a dedicated phylowgs subdirectory
echo "Creating logs directory: ${PHYLOWGS_LOGS_DIR}" >&2
mkdir -p "${PHYLOWGS_LOGS_DIR}"

# Set log file paths using absolute paths
LOG_FILE="${PHYLOWGS_LOGS_DIR}/${BOOTSTRAP_DIR_NAME}.log"
ERR_FILE="${PHYLOWGS_LOGS_DIR}/${BOOTSTRAP_DIR_NAME}.err"

echo "Redirecting output to: ${LOG_FILE}" >&2
echo "Redirecting errors to: ${ERR_FILE}" >&2

# Redirect output to absolute log paths
exec > "${LOG_FILE}" 2> "${ERR_FILE}"

echo "--- PhyloWGS Processing for Bootstrap Sample: $BOOTSTRAP_DIR_NAME ---"
echo "Job ID: $SLURM_JOB_ID, Array Task ID: $SLURM_ARRAY_TASK_ID"
echo "Working Directory: $(pwd)"
echo "Bootstrap Directory: $CURRENT_BOOTSTRAP_DIR_PATH"
echo "Bootstrap Number: $BOOTSTRAP_NUM"
echo "Code Directory: $CODE_DIR"
echo "Log Directory: $PHYLOWGS_LOGS_DIR"

SSM_FILE="${CURRENT_BOOTSTRAP_DIR_PATH}/ssm.txt"
CNV_FILE="${CURRENT_BOOTSTRAP_DIR_PATH}/cnv.txt"
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
# Explicit successful exit to ensure dependency is satisfied
exit 0