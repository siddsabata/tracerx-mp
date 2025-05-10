#!/bin/bash
# run_pipeline.sh - Master script to orchestrate the TracerX marker selection pipeline
# Usage: ./run_pipeline.sh <patient_id> <input_ssm_file> <pipeline_output_base_dir> [num_bootstraps] [read_depth]

set -e  # Exit on any error

# --- Input Validation ---
if [ "$#" -lt 3 ] || [ "$#" -gt 5 ]; then
    echo "Error: Incorrect number of arguments."
    echo "Usage: $0 <patient_id> <input_ssm_file> <pipeline_output_base_dir> [num_bootstraps] [read_depth]"
    echo "Example: $0 CRUK0001 /path/to/data/CRUK0001/ssm.txt /path/to/output/CRUK0001 100 1500"
    exit 1
fi

# --- Parse Arguments ---
PATIENT_ID=$1
INPUT_SSM_FILE=$2
PIPELINE_OUTPUT_BASE_DIR=$3
NUM_BOOTSTRAPS=${4:-100}  # Default to 100 if not provided
READ_DEPTH=${5:-1500}     # Default to 1500 if not provided

# --- Validate Input Files/Directories ---
if [ ! -f "$INPUT_SSM_FILE" ]; then
    echo "Error: Input SSM file not found: $INPUT_SSM_FILE"
    exit 1
fi

# --- Define Derived Paths ---
BOOTSTRAP_STAGE_OUTPUT_DIR="${PIPELINE_OUTPUT_BASE_DIR}"
BOOTSTRAPS_DATA_DIR="${BOOTSTRAP_STAGE_OUTPUT_DIR}/bootstraps"
AGGREGATION_RESULTS_DIR="${BOOTSTRAP_STAGE_OUTPUT_DIR}/aggregation_results"
LOG_DIR="${PIPELINE_OUTPUT_BASE_DIR}/logs"

# --- Create Required Directories ---
mkdir -p "${LOG_DIR}"
mkdir -p "${BOOTSTRAP_STAGE_OUTPUT_DIR}"

# --- Logging Setup ---
MASTER_LOG="${LOG_DIR}/pipeline_master.log"
exec > >(tee -a "${MASTER_LOG}") 2>&1

echo "=== Pipeline Start: $(date) ==="
echo "Patient ID: ${PATIENT_ID}"
echo "Input SSM: ${INPUT_SSM_FILE}"
echo "Output Base: ${PIPELINE_OUTPUT_BASE_DIR}"
echo "Number of Bootstraps: ${NUM_BOOTSTRAPS}"
echo "Read Depth: ${READ_DEPTH}"
echo "Log Directory: ${LOG_DIR}"
echo "----------------------------------------"

# --- Function to Submit Job and Check Status ---
submit_job() {
    local job_name=$1
    local dependency=$2
    local script=$3
    shift 3
    local args=("$@")
    
    local dependency_flag=""
    if [ ! -z "$dependency" ]; then
        dependency_flag="--dependency=afterok:${dependency}"
    fi
    
    echo "Submitting ${job_name}..."
    local job_id=$(sbatch --parsable \
        --job-name="${PATIENT_ID}_${job_name}" \
        --output="${LOG_DIR}/slurm_${job_name}_%j.out" \
        --error="${LOG_DIR}/slurm_${job_name}_%j.err" \
        ${dependency_flag} \
        "${script}" "${args[@]}")
    
    if [ -z "${job_id}" ]; then
        echo "Error: Failed to submit ${job_name} job"
        exit 1
    fi
    
    echo "${job_name} job submitted with ID: ${job_id}"
    echo "${job_id}"
}

# --- Step 1: Bootstrap ---
echo "Starting Bootstrap Stage..."
BOOTSTRAP_JOB_ID=$(submit_job "bootstrap" "" \
    "./1-bootstrap/bootstrap.sh" \
    "${INPUT_SSM_FILE}" "${BOOTSTRAP_STAGE_OUTPUT_DIR}" "${NUM_BOOTSTRAPS}")

# --- Step 2: PhyloWGS (Array Job) ---
echo "Starting PhyloWGS Stage..."
PHYLOWGS_JOB_ID=$(submit_job "phylowgs" "${BOOTSTRAP_JOB_ID}" \
    "./2-phylowgs/phylowgs.sh" \
    "${BOOTSTRAPS_DATA_DIR}")

# --- Step 3: Aggregation ---
echo "Starting Aggregation Stage..."
AGGREGATION_JOB_ID=$(submit_job "aggregation" "${PHYLOWGS_JOB_ID}" \
    "./3-aggregation/aggregation.sh" \
    "${PATIENT_ID}" "${BOOTSTRAPS_DATA_DIR}")

# --- Step 4: Marker Selection ---
echo "Starting Marker Selection Stage..."
MARKER_SELECTION_JOB_ID=$(submit_job "marker_selection" "${AGGREGATION_JOB_ID}" \
    "./4-markers/marker_selection.sh" \
    "${PATIENT_ID}" "${AGGREGATION_RESULTS_DIR}" "${INPUT_SSM_FILE}" "${READ_DEPTH}")

# --- Final Status ---
echo "----------------------------------------"
echo "Pipeline submitted successfully!"
echo "Final marker selection job ID: ${MARKER_SELECTION_JOB_ID}"
echo "Monitor progress with: squeue -u $USER"
echo "Check logs in: ${LOG_DIR}"
echo "=== Pipeline Submission Complete: $(date) ==="

# --- Save Job IDs for Reference ---
cat > "${LOG_DIR}/job_ids.txt" << EOF
Pipeline Job IDs for ${PATIENT_ID}:
Bootstrap: ${BOOTSTRAP_JOB_ID}
PhyloWGS: ${PHYLOWGS_JOB_ID}
Aggregation: ${AGGREGATION_JOB_ID}
Marker Selection: ${MARKER_SELECTION_JOB_ID}
EOF