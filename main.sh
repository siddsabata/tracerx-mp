#!/bin/bash
#
# TracerX Marker Selection Pipeline - Main Orchestration Script
# 
# This script submits all pipeline stages as Slurm jobs with proper dependencies
# to ensure sequential execution: bootstrap -> phylowgs -> aggregation -> markers
#
# Usage: ./main.sh <patient_id> <input_ssm_file> <output_base_dir> [num_bootstraps] [read_depth]
#

set -e  # Exit immediately if any command fails

# --- Input Validation ---
if [ "$#" -lt 3 ] || [ "$#" -gt 5 ]; then
    echo "Error: Incorrect number of arguments."
    echo ""
    echo "Usage: $0 <patient_id> <input_ssm_file> <output_base_dir> [num_bootstraps] [read_depth]"
    echo ""
    echo "Arguments:"
    echo "  patient_id        - Patient identifier (e.g., CRUK0044)"
    echo "  input_ssm_file    - Path to input SSM file"
    echo "  output_base_dir   - Base directory for all pipeline outputs"
    echo "  num_bootstraps    - Number of bootstrap samples (default: 100)"
    echo "  read_depth        - Read depth for marker selection (default: 1500)"
    echo ""
    echo "Example:"
    echo "  $0 CRUK0044 data/ssm.txt /path/to/output 100 1500"
    echo ""
    exit 1
fi

# --- Parse and validate arguments ---
PATIENT_ID="$1"
INPUT_SSM_FILE="$2"
OUTPUT_BASE_DIR="$3"
NUM_BOOTSTRAPS="${4:-100}"
READ_DEPTH="${5:-1500}"

# Get absolute path to the code directory (where this script is located)
CODE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Convert input paths to absolute paths
if [[ ! "$INPUT_SSM_FILE" = /* ]]; then
    INPUT_SSM_FILE="$(cd "$(dirname "$INPUT_SSM_FILE")" && pwd)/$(basename "$INPUT_SSM_FILE")"
fi

if [[ ! "$OUTPUT_BASE_DIR" = /* ]]; then
    OUTPUT_BASE_DIR="$(cd "$(dirname "$OUTPUT_BASE_DIR")" && pwd)/$(basename "$OUTPUT_BASE_DIR")"
fi

# Validate inputs
if [ ! -f "$INPUT_SSM_FILE" ]; then
    echo "Error: Input SSM file not found: $INPUT_SSM_FILE"
    exit 1
fi

if [ ! -d "$CODE_DIR" ]; then
    echo "Error: Code directory not found: $CODE_DIR"
    exit 1
fi

# Validate numeric arguments
if ! [[ "$NUM_BOOTSTRAPS" =~ ^[0-9]+$ ]] || [ "$NUM_BOOTSTRAPS" -lt 1 ]; then
    echo "Error: num_bootstraps must be a positive integer"
    exit 1
fi

if ! [[ "$READ_DEPTH" =~ ^[0-9]+$ ]] || [ "$READ_DEPTH" -lt 1 ]; then
    echo "Error: read_depth must be a positive integer"
    exit 1
fi

# --- Setup directory structure ---
INITIAL_DIR="${OUTPUT_BASE_DIR}/initial"
BOOTSTRAPS_DIR="${INITIAL_DIR}/bootstraps"
AGGREGATION_DIR="${INITIAL_DIR}/aggregation_results"
MARKERS_DIR="${INITIAL_DIR}/markers"
LOGS_DIR="${INITIAL_DIR}/logs"

# Create all required directories
mkdir -p "$OUTPUT_BASE_DIR"
mkdir -p "$INITIAL_DIR"
mkdir -p "$BOOTSTRAPS_DIR"
mkdir -p "$AGGREGATION_DIR"
mkdir -p "$MARKERS_DIR"
mkdir -p "$LOGS_DIR"

# --- Setup logging ---
MASTER_LOG="${LOGS_DIR}/pipeline_master.log"
JOB_IDS_FILE="${LOGS_DIR}/job_ids.txt"

# Start logging
{
    echo "=== TracerX Pipeline Orchestration Started: $(date) ==="
    echo "Patient ID: $PATIENT_ID"
    echo "Input SSM file: $INPUT_SSM_FILE"
    echo "Output base directory: $OUTPUT_BASE_DIR"
    echo "Code directory: $CODE_DIR"
    echo "Number of bootstraps: $NUM_BOOTSTRAPS"
    echo "Read depth: $READ_DEPTH"
    echo "Initial processing directory: $INITIAL_DIR"
    echo "Logs directory: $LOGS_DIR"
    echo ""
} | tee "$MASTER_LOG"

# --- Helper function to submit jobs with proper error handling ---
submit_job() {
    local stage_name="$1"
    local script_path="$2"
    local dependency_job_id="$3"
    shift 3
    local job_args=("$@")
    
    echo "=== Submitting $stage_name stage ===" | tee -a "$MASTER_LOG"
    echo "Script: $script_path" | tee -a "$MASTER_LOG"
    echo "Arguments: ${job_args[*]}" | tee -a "$MASTER_LOG"
    
    # Validate script exists
    if [ ! -f "$script_path" ]; then
        echo "Error: Script not found: $script_path" | tee -a "$MASTER_LOG"
        exit 1
    fi
    
    # Build sbatch command
    local sbatch_cmd=(
        sbatch
        --parsable
        --job-name="${PATIENT_ID}_${stage_name}"
        --output="${LOGS_DIR}/slurm_${stage_name}_%j.out"
        --error="${LOGS_DIR}/slurm_${stage_name}_%j.err"
    )
    
    # Add dependency if specified
    if [ -n "$dependency_job_id" ]; then
        sbatch_cmd+=(--dependency="afterok:$dependency_job_id")
        echo "Dependency: afterok:$dependency_job_id" | tee -a "$MASTER_LOG"
    fi
    
    # Add script and arguments
    sbatch_cmd+=("$script_path")
    sbatch_cmd+=("${job_args[@]}")
    
    # Submit job and capture output
    local job_output
    job_output=$("${sbatch_cmd[@]}" 2>&1)
    local submit_status=$?
    
    if [ $submit_status -ne 0 ]; then
        echo "Error: Failed to submit $stage_name job" | tee -a "$MASTER_LOG"
        echo "sbatch output: $job_output" | tee -a "$MASTER_LOG"
        exit 1
    fi
    
    # Extract job ID (sbatch --parsable returns just the job ID)
    local job_id="$job_output"
    
    # Validate job ID is numeric
    if ! [[ "$job_id" =~ ^[0-9]+$ ]]; then
        echo "Error: Invalid job ID returned: $job_id" | tee -a "$MASTER_LOG"
        exit 1
    fi
    
    echo "Job submitted successfully with ID: $job_id" | tee -a "$MASTER_LOG"
    echo "$stage_name: $job_id" >> "$JOB_IDS_FILE"
    echo "" | tee -a "$MASTER_LOG"
    
    # Return job ID
    echo "$job_id"
}

# --- Stage 1: Bootstrap ---
echo "Starting pipeline execution..." | tee -a "$MASTER_LOG"

BOOTSTRAP_JOB_ID=$(submit_job "bootstrap" \
    "${CODE_DIR}/1-bootstrap/bootstrap.sh" \
    "" \
    "$INPUT_SSM_FILE" "$INITIAL_DIR" "$CODE_DIR" "$NUM_BOOTSTRAPS")

# --- Stage 2: PhyloWGS ---
# PhyloWGS uses array jobs, so we need to submit with dynamic array size
# Array indices are 0-based, so for N bootstraps we need array 0-(N-1)
PHYLOWGS_ARRAY_MAX=$((NUM_BOOTSTRAPS - 1))

echo "=== Submitting phylowgs stage ===" | tee -a "$MASTER_LOG"
echo "Script: ${CODE_DIR}/2-phylowgs/phylowgs.sh" | tee -a "$MASTER_LOG"
echo "Arguments: $BOOTSTRAPS_DIR $CODE_DIR" | tee -a "$MASTER_LOG"
echo "Array range: 0-$PHYLOWGS_ARRAY_MAX" | tee -a "$MASTER_LOG"

# Validate script exists
if [ ! -f "${CODE_DIR}/2-phylowgs/phylowgs.sh" ]; then
    echo "Error: Script not found: ${CODE_DIR}/2-phylowgs/phylowgs.sh" | tee -a "$MASTER_LOG"
    exit 1
fi

# Add dependency if specified
DEPENDENCY_FLAG=""
if [ -n "$BOOTSTRAP_JOB_ID" ]; then
    DEPENDENCY_FLAG="--dependency=afterok:$BOOTSTRAP_JOB_ID"
    echo "Dependency: afterok:$BOOTSTRAP_JOB_ID" | tee -a "$MASTER_LOG"
fi

# Submit PhyloWGS array job with dynamic array size
PHYLOWGS_JOB_OUTPUT=$(sbatch --parsable \
    --job-name="${PATIENT_ID}_phylowgs" \
    --output="${LOGS_DIR}/slurm_phylowgs_%A_%a.out" \
    --error="${LOGS_DIR}/slurm_phylowgs_%A_%a.err" \
    --array="0-${PHYLOWGS_ARRAY_MAX}%10" \
    $DEPENDENCY_FLAG \
    "${CODE_DIR}/2-phylowgs/phylowgs.sh" \
    "$BOOTSTRAPS_DIR" "$CODE_DIR" 2>&1)

PHYLOWGS_SUBMIT_STATUS=$?
if [ $PHYLOWGS_SUBMIT_STATUS -ne 0 ]; then
    echo "Error: Failed to submit phylowgs job" | tee -a "$MASTER_LOG"
    echo "sbatch output: $PHYLOWGS_JOB_OUTPUT" | tee -a "$MASTER_LOG"
    exit 1
fi

PHYLOWGS_JOB_ID="$PHYLOWGS_JOB_OUTPUT"

# Validate job ID is numeric
if ! [[ "$PHYLOWGS_JOB_ID" =~ ^[0-9]+$ ]]; then
    echo "Error: Invalid job ID returned: $PHYLOWGS_JOB_ID" | tee -a "$MASTER_LOG"
    exit 1
fi

echo "Job submitted successfully with ID: $PHYLOWGS_JOB_ID" | tee -a "$MASTER_LOG"
echo "phylowgs: $PHYLOWGS_JOB_ID" >> "$JOB_IDS_FILE"
echo "" | tee -a "$MASTER_LOG"

# --- Stage 3: Aggregation ---
AGGREGATION_JOB_ID=$(submit_job "aggregation" \
    "${CODE_DIR}/3-aggregation/aggregation.sh" \
    "$PHYLOWGS_JOB_ID" \
    "$PATIENT_ID" "$BOOTSTRAPS_DIR" "$CODE_DIR")

# --- Stage 4: Marker Selection ---
MARKER_SELECTION_JOB_ID=$(submit_job "marker_selection" \
    "${CODE_DIR}/4-markers/marker_selection.sh" \
    "$AGGREGATION_JOB_ID" \
    "$PATIENT_ID" "$AGGREGATION_DIR" "$INPUT_SSM_FILE" "$CODE_DIR" "$READ_DEPTH")

# --- Pipeline submission complete ---
{
    echo "=== Pipeline Submission Complete: $(date) ==="
    echo ""
    echo "All jobs submitted successfully!"
    echo ""
    echo "Job IDs:"
    echo "  Bootstrap:        $BOOTSTRAP_JOB_ID"
    echo "  PhyloWGS:         $PHYLOWGS_JOB_ID"
    echo "  Aggregation:      $AGGREGATION_JOB_ID"
    echo "  Marker Selection: $MARKER_SELECTION_JOB_ID"
    echo ""
    echo "Monitor progress with:"
    echo "  squeue -u \$USER"
    echo "  squeue -j $BOOTSTRAP_JOB_ID,$PHYLOWGS_JOB_ID,$AGGREGATION_JOB_ID,$MARKER_SELECTION_JOB_ID"
    echo ""
    echo "Check logs in: $LOGS_DIR"
    echo "Job IDs saved to: $JOB_IDS_FILE"
    echo ""
    echo "Pipeline will process $NUM_BOOTSTRAPS bootstrap samples"
    echo "Final results will be in: $MARKERS_DIR"
    echo ""
} | tee -a "$MASTER_LOG"

# --- Save pipeline configuration for reference ---
cat > "${LOGS_DIR}/pipeline_config.txt" << EOF
TracerX Pipeline Configuration
==============================
Execution Date: $(date)
Patient ID: $PATIENT_ID
Input SSM File: $INPUT_SSM_FILE
Output Base Directory: $OUTPUT_BASE_DIR
Code Directory: $CODE_DIR
Number of Bootstraps: $NUM_BOOTSTRAPS
Read Depth: $READ_DEPTH

Directory Structure:
- Initial Directory: $INITIAL_DIR
- Bootstraps Directory: $BOOTSTRAPS_DIR
- Aggregation Directory: $AGGREGATION_DIR
- Markers Directory: $MARKERS_DIR
- Logs Directory: $LOGS_DIR

Job Dependencies:
Bootstrap -> PhyloWGS -> Aggregation -> Marker Selection
EOF

echo "Pipeline configuration saved to: ${LOGS_DIR}/pipeline_config.txt" | tee -a "$MASTER_LOG"
echo "=== Orchestration script completed successfully ===" | tee -a "$MASTER_LOG" 