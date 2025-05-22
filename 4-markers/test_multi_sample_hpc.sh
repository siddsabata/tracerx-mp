#!/bin/bash
#
# Test script for running multi-sample marker selection on HPC
# This script provides examples of how to submit the multi-sample marker selection job
#

# Set these paths according to your HPC setup
PATIENT_ID="CRUK0044"
AGGREGATION_DIR="/path/to/patient/data/CRUK0044/initial/aggregation_results"
SSM_FILE="/path/to/patient/data/CRUK0044/ssm.txt"
CODE_DIR="/path/to/tracerx-mp"

# Default parameters
READ_DEPTH=1500
FILTER_STRATEGY="any_high"
FILTER_THRESHOLD=0.9

echo "Multi-sample Marker Selection Test Script"
echo "========================================="
echo ""
echo "Before running, please update the paths in this script:"
echo "  PATIENT_ID: $PATIENT_ID"
echo "  AGGREGATION_DIR: $AGGREGATION_DIR"
echo "  SSM_FILE: $SSM_FILE"
echo "  CODE_DIR: $CODE_DIR"
echo ""

# Check if paths look like they need updating
if [[ "$AGGREGATION_DIR" == *"/path/to/"* ]]; then
    echo "ERROR: Please update the paths in this script before running!"
    echo "Edit the variables at the top of $0"
    exit 1
fi

echo "Test 1: Basic run with default parameters (any_high strategy)"
echo "Command:"
echo "sbatch ${CODE_DIR}/4-markers/marker_selection.sh \\"
echo "    \"$PATIENT_ID\" \\"
echo "    \"$AGGREGATION_DIR\" \\"
echo "    \"$SSM_FILE\" \\"
echo "    \"$CODE_DIR\" \\"
echo "    $READ_DEPTH \\"
echo "    \"$FILTER_STRATEGY\" \\"
echo "    $FILTER_THRESHOLD"
echo ""

read -p "Submit this job? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sbatch "${CODE_DIR}/4-markers/marker_selection.sh" \
        "$PATIENT_ID" \
        "$AGGREGATION_DIR" \
        "$SSM_FILE" \
        "$CODE_DIR" \
        $READ_DEPTH \
        "$FILTER_STRATEGY" \
        $FILTER_THRESHOLD
    echo "Job submitted!"
else
    echo "Job not submitted."
fi

echo ""
echo "Other example commands you can try:"
echo ""
echo "# Test with all_high strategy (less restrictive filtering):"
echo "sbatch ${CODE_DIR}/4-markers/marker_selection.sh \\"
echo "    \"$PATIENT_ID\" \"$AGGREGATION_DIR\" \"$SSM_FILE\" \"$CODE_DIR\" \\"
echo "    1500 \"all_high\" 0.9"
echo ""
echo "# Test with majority_high strategy:"
echo "sbatch ${CODE_DIR}/4-markers/marker_selection.sh \\"
echo "    \"$PATIENT_ID\" \"$AGGREGATION_DIR\" \"$SSM_FILE\" \"$CODE_DIR\" \\"
echo "    1500 \"majority_high\" 0.8"
echo ""
echo "# Test with specific samples (samples 0 and 2):"
echo "sbatch ${CODE_DIR}/4-markers/marker_selection.sh \\"
echo "    \"$PATIENT_ID\" \"$AGGREGATION_DIR\" \"$SSM_FILE\" \"$CODE_DIR\" \\"
echo "    1500 \"specific_samples\" 0.9 \"0 2\""
echo ""
echo "Monitor job status with: squeue -u \$USER"
echo "Check logs in: \$AGGREGATION_DIR/../logs/" 