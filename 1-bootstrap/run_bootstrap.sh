#!/bin/bash
# --------------------------------------------------
# This script performs bootstrapping on mutation data.
#
# It performs:
#  1. Bootstrapping via bootstrap.py on the provided mutation data CSV
#  2. Creates bootstrap replicate samples for further analysis with PhyloWGS
#
# Usage:
#   ./run_bootstrap.sh <input_directory> [num_bootstraps]
#
# Example:
#   ./run_bootstrap.sh /data/tracerx_2017/CRUK0044/initial 100
#
# Note:
#   Ensure the conda environment with the required dependencies 
#   is activated before executing this script.
# --------------------------------------------------

# Enable strict error handling
set -e

# Get the directory containing this script
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check for input directory argument
if [ -z "$1" ]; then
    echo "Usage: $0 <input_directory> [num_bootstraps]"
    exit 1
fi

input_dir="$1"
num_bootstraps="${2:-100}"
dir_name=$(basename "$input_dir")

echo "---------------------------------------"
echo "[$(date)] Starting bootstrap process"
echo "Input directory: ${input_dir}"
echo "Number of bootstraps: ${num_bootstraps}"
echo "---------------------------------------"

# Validate input directory exists
if [ ! -d "$input_dir" ]; then
    echo "Error: Input directory ${input_dir} does not exist"
    exit 1
fi

# Find the CSV file - try to find one with matching directory name first, otherwise take any CSV
csv_file=$(find "$input_dir" -name "*${dir_name}*.csv" -type f | head -n 1)
if [ -z "$csv_file" ]; then
    csv_file=$(find "$input_dir" -name "*.csv" -type f | head -n 1)
fi

if [ -z "$csv_file" ]; then
    echo "Error: No CSV file found in ${input_dir}"
    exit 1
fi

echo "Found CSV file: ${csv_file}"

# Create marker file directory if it doesn't exist
mkdir -p "${input_dir}/.markers"

# Run bootstrap processing
echo "[$(date)] Running bootstrap processing with ${num_bootstraps} iterations..."
python "${script_dir}/bootstrap.py" --input "${csv_file}" --output "${input_dir}" --num_bootstraps "${num_bootstraps}"

# Create completion marker
touch "${input_dir}/.markers/bootstrap_complete"

# Count generated bootstrap directories
bootstrap_count=$(find "${input_dir}" -type d -name "bootstrap*" | wc -l)
echo "[$(date)] Generated ${bootstrap_count} bootstrap samples"

# Verify all bootstrap directories contain required files
echo "Verifying bootstrap outputs..."
missing_files=0
for i in $(seq 1 ${num_bootstraps}); do
    bootstrap_dir="${input_dir}/bootstrap${i}"
    if [ ! -d "${bootstrap_dir}" ]; then
        echo "Warning: Bootstrap directory ${i} not found"
        missing_files=$((missing_files + 1))
        continue
    fi
    
    if [ ! -f "${bootstrap_dir}/ssm_data_bootstrap${i}.txt" ]; then
        echo "Warning: Missing SSM file in bootstrap ${i}"
        missing_files=$((missing_files + 1))
    fi
    
    if [ ! -f "${bootstrap_dir}/cnv_data_bootstrap${i}.txt" ]; then
        echo "Warning: Missing CNV file in bootstrap ${i}"
        missing_files=$((missing_files + 1))
    fi
done

if [ ${missing_files} -gt 0 ]; then
    echo "Warning: ${missing_files} missing files detected in bootstrap outputs"
else
    echo "All bootstrap outputs verified successfully!"
fi

echo "[$(date)] Bootstrapping completed successfully for ${dir_name}." 