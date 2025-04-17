#!/bin/bash
#SBATCH --job-name=phylowgs
#SBATCH --partition=pool1
#SBATCH --cpus-per-task=5
#SBATCH --mem=8G
#SBATCH --array=0-3

# Usage: sbatch phylowgs.sh <directory of preprocessed data>
BASE_DIR=$1

# activate phylowgs environment
source ~/miniconda3/bin/activate phylowgs_env

phylowgs_dir="$(pwd)/2-phylowgs/phylowgs"
multievolve="${phylowgs_dir}/multievolve.py"
write_results="${phylowgs_dir}/write_results.py"

# list of all patient directories
PATIENT_DIRS=($(ls -d ${BASE_DIR}/CRUK*))

# patient dir for this array task 
PATIENT_DIR="${PATIENT_DIRS[$SLURM_ARRAY_TASK_ID]}"
PATIENT_ID=$(basename "$PATIENT_DIR")

# Create patient-specific log directory and redirect output
mkdir -p "${PATIENT_DIR}/logs"
exec > "${PATIENT_DIR}/logs/phylowgs.log" 2> "${PATIENT_DIR}/logs/phylowgs.err"

echo "Processing patient: $PATIENT_ID"

# run phylowgs
python2 "${multievolve}" --num-chains 5 \
        --ssms "${PATIENT_DIR}/initial/ssm.txt" \
        --cnvs "${PATIENT_DIR}/initial/cnv.txt" \
        --output-dir "${PATIENT_DIR}/initial/chains"

python2 "${write_results}" --include-ssm-names result \
                "${PATIENT_DIR}/initial/chains/trees.zip" \
                "${PATIENT_DIR}/initial/result.summ.json.gz" \
                "${PATIENT_DIR}/initial/result.muts.json.gz" \
                "${PATIENT_DIR}/initial/result.mutass.zip"