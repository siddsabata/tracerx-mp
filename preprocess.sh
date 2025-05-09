#!/bin/bash
#SBATCH --job-name=preprocess
#SBATCH --output=logs/preprocess_%j.out
#SBATCH --error=logs/preprocess_%j.err
#SBATCH --partition=pool1
#SBATCH --cpus-per-task=5
#SBATCH --mem=16G

# usage: sbatch preprocess.sh <mutation csv> <output directory>

# Check if both input and output directories are provided
if [ $# -ne 2 ]; then
    echo "Error: Both input and output paths must be provided"
    echo "Usage: sbatch $0 <input_csv> <output_directory>"
    exit 1
fi

INPUT_CSV=$1
OUTPUT_DIR=$2
# Define the patient ID to be processed.
# This is currently hardcoded as in the existing script.
# If you need to process multiple patients or make this dynamic, this part would need changes.
PATIENT_ID="CRUK0044"

# Create logs directory if it doesn't exist
mkdir -p logs

# activate preprocess environment
source ~/miniconda3/bin/activate preprocess_env

# run preprocess.py
echo "Running main preprocessing script (process_tracerX.py) for patient $PATIENT_ID..."
python3 0-preprocess/process_tracerX.py -i "$INPUT_CSV" -o "$OUTPUT_DIR" -p "$PATIENT_ID"

# Define paths for the bootstrapping step
# Input CSV for bootstrap.py is the patient-specific initial CSV from process_tracerX.py
BOOTSTRAP_INPUT_CSV="${OUTPUT_DIR}/${PATIENT_ID}/initial/${PATIENT_ID}_initial.csv"
# Output directory for bootstrap.py results
BOOTSTRAP_OUTPUT_DIR="${OUTPUT_DIR}/${PATIENT_ID}/bootstrap_data"

# Ensure the main output directory for bootstrapping exists
# bootstrap.py will create subdirectories like 'bootstrap1', 'bootstrap2', etc. inside this.
mkdir -p "$BOOTSTRAP_OUTPUT_DIR"

echo "Running bootstrapping script (bootstrap.py) for patient $PATIENT_ID..."
echo "Bootstrap input file: $BOOTSTRAP_INPUT_CSV"
echo "Bootstrap output directory: $BOOTSTRAP_OUTPUT_DIR"

# Run the bootstrap script
# It's assumed that bootstrap.py is executable and its dependencies are in preprocess_env
python3 1-bootstrap/bootstrap.py \
    -i "$BOOTSTRAP_INPUT_CSV" \
    -o "$BOOTSTRAP_OUTPUT_DIR" \
    -n 100

echo "Preprocessing and bootstrapping for patient $PATIENT_ID completed."
echo "Bootstrapped files should be in $BOOTSTRAP_OUTPUT_DIR"