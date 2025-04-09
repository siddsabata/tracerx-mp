#!/bin/bash
#SBATCH --job-name=preprocess
#SBATCH --output=logs/preprocess_%j.out
#SBATCH --error=logs/preprocess_%j.err
#SBATCH --partition=pool1
#SBATCH --cpus-per-task=5
#SBATCH --mem=16G

# activate preprocess environment
conda init
conda activate preprocess_env

# run preprocess.py
python3 0-preprocess/process_tracerx.py -i data/tracerx_2023_init.csv -o output 