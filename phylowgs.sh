#!/bin/bash
#SBATCH --job-name=phylowgs
#SBATCH --output=logs/preprocess_A_%j.out
#SBATCH --error=logs/preprocess_A_%j.err
#SBATCH --partition=pool1
#SBATCH --cpus-per-task=5
#SBATCH --mem=8G
#SBATCH --array=0-20%10

# activate phylowgs environment
source activate phylowgs

phylowgs_dir="$(pwd)/2-phylowgs/phylowgs"
multievolve="${phylowgs_dir}/multievolve.py"
write_results="${phylowgs_dir}/write_results.py"

# list of all patient directories
BASE_DIR="./output"
PATIENT_DIRS=($(ls -d ${BASE_DIR}/CRUK*))

# patient dir for this array task 
PATIENT_DIR="${PATIENT_DIRS[$SLURM_ARRAY_TASK_ID]}"
PATIENT_ID=$(basename "$PATIENT_DIR")

echo "Processing patient: $PATIENT_ID"
echo "Directory: $PATIENT_DIR"

# run phylowgs 
python2 "${multievolve}" --num-chains 5 \
        --ssms "${PATIENT_DIR}/initial/ssm.txt" \
        --cnvs "${PATIENT_DIR}/initial/cnv.txt"
python2 "${write_results}" --include-ssm-names result \
                "${PATIENT_DIR}/initial/trees.zip" \
                "${PATIENT_DIR}/initial/result.summ.json.gz" \
                "${PATIENT_DIR}/initial/result.muts.json.gz" \
                "${PATIENT_DIR}/initial/result.mutass.zip"