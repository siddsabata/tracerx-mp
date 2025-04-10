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

# Create logs directory if it doesn't exist
mkdir -p logs

# activate preprocess environment
source ~/miniconda3/bin/activate preprocess_env

# run preprocess.py
python3 0-preprocess/process_tracerX.py -i "$INPUT_CSV" -o "$OUTPUT_DIR" 