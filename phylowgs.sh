#!/bin/bash
#SBATCH --job-name=phylowgs
#SBATCH --output=logs/phylowgs_%A_%j.out
#SBATCH --error=logs/phylowgs_%A_%j.err
#SBATCH --partition=pool1
#SBATCH --cpus-per-task=5
#SBATCH --mem=8G
#SBATCH --array=0-19%10

# example usage:
# sbatch run_phylowgs.sh /path/to/output/directory

BASE_DIR=$1

# activate phylowgs environment
source ~/miniconda3/bin/activate phylowgs_env

phylowgs_dir="$(pwd)/2-phylowgs/phylowgs"
multievolve="${phylowgs_dir}/multievolve.py"
write_results="${phylowgs_dir}/write_results.py"

# list of all patient directories
PATIENT_DIRS=($(ls -d ${BASE_DIR}/CRUK*))

# Check if any patient directories were found
if [ ${#PATIENT_DIRS[@]} -eq 0 ]; then
    echo "Error: No patient directories found in $BASE_DIR"
    exit 1
fi

# patient dir for this array task 
PATIENT_DIR="${PATIENT_DIRS[$SLURM_ARRAY_TASK_ID]}"
PATIENT_ID=$(basename "$PATIENT_DIR")

echo "Processing patient: $PATIENT_ID"
echo "Directory: $PATIENT_DIR"

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