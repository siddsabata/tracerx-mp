#!/bin/bash
#
# TracerX Pipeline Monitor Script
# 
# This script helps monitor the progress of a running TracerX pipeline
# by checking job status and providing useful information about each stage.
#
# Usage: ./monitor_pipeline.sh <logs_directory>
#

set -e

if [ "$#" -ne 1 ]; then
    echo "Error: Incorrect number of arguments."
    echo ""
    echo "Usage: $0 <logs_directory>"
    echo ""
    echo "Example:"
    echo "  $0 /path/to/output/initial/logs"
    echo ""
    exit 1
fi

LOGS_DIR="$1"
JOB_IDS_FILE="${LOGS_DIR}/job_ids.txt"
MASTER_LOG="${LOGS_DIR}/pipeline_master.log"

# Validate inputs
if [ ! -d "$LOGS_DIR" ]; then
    echo "Error: Logs directory not found: $LOGS_DIR"
    exit 1
fi

if [ ! -f "$JOB_IDS_FILE" ]; then
    echo "Error: Job IDs file not found: $JOB_IDS_FILE"
    echo "Make sure the pipeline has been started and the logs directory is correct."
    exit 1
fi

echo "=== TracerX Pipeline Monitor ==="
echo "Logs directory: $LOGS_DIR"
echo "Timestamp: $(date)"
echo ""

# Read job IDs
echo "=== Job Status ==="
if [ -f "$JOB_IDS_FILE" ]; then
    echo "Job IDs from: $JOB_IDS_FILE"
    cat "$JOB_IDS_FILE"
    echo ""
    
    # Extract job IDs for squeue command
    JOB_IDS=$(grep -E "^[a-zA-Z_]+:" "$JOB_IDS_FILE" | cut -d: -f2 | tr '\n' ',' | sed 's/,$//')
    
    if [ -n "$JOB_IDS" ]; then
        echo "Current job status:"
        squeue -j "$JOB_IDS" 2>/dev/null || echo "No jobs found in queue (may have completed or failed)"
        echo ""
    fi
else
    echo "Job IDs file not found."
fi

# Check for recent log activity
echo "=== Recent Log Activity ==="
if [ -f "$MASTER_LOG" ]; then
    echo "Last 10 lines from master log:"
    tail -10 "$MASTER_LOG"
    echo ""
else
    echo "Master log not found."
fi

# Check individual stage logs
echo "=== Stage-Specific Logs ==="

# Bootstrap logs
BOOTSTRAP_LOG="${LOGS_DIR}/bootstrap_execution.log"
if [ -f "$BOOTSTRAP_LOG" ]; then
    echo "Bootstrap stage: Log found"
    BOOTSTRAP_LINES=$(wc -l < "$BOOTSTRAP_LOG")
    echo "  - Log lines: $BOOTSTRAP_LINES"
    if [ $BOOTSTRAP_LINES -gt 0 ]; then
        echo "  - Last line: $(tail -1 "$BOOTSTRAP_LOG")"
    fi
else
    echo "Bootstrap stage: No log found"
fi

# PhyloWGS logs (array job - check for any logs)
PHYLOWGS_LOGS=$(find "$LOGS_DIR" -name "slurm_phylowgs_*.out" 2>/dev/null | wc -l)
if [ $PHYLOWGS_LOGS -gt 0 ]; then
    echo "PhyloWGS stage: $PHYLOWGS_LOGS log files found"
    # Check a sample log for progress
    SAMPLE_LOG=$(find "$LOGS_DIR" -name "slurm_phylowgs_*.out" 2>/dev/null | head -1)
    if [ -f "$SAMPLE_LOG" ]; then
        SAMPLE_LINES=$(wc -l < "$SAMPLE_LOG")
        echo "  - Sample log lines: $SAMPLE_LINES"
        if [ $SAMPLE_LINES -gt 0 ]; then
            echo "  - Sample last line: $(tail -1 "$SAMPLE_LOG")"
        fi
    fi
else
    echo "PhyloWGS stage: No logs found"
fi

# Aggregation logs
AGGREGATION_LOG="${LOGS_DIR}/aggregation_execution.log"
if [ -f "$AGGREGATION_LOG" ]; then
    echo "Aggregation stage: Log found"
    AGGREGATION_LINES=$(wc -l < "$AGGREGATION_LOG")
    echo "  - Log lines: $AGGREGATION_LINES"
    if [ $AGGREGATION_LINES -gt 0 ]; then
        echo "  - Last line: $(tail -1 "$AGGREGATION_LOG")"
    fi
else
    echo "Aggregation stage: No log found"
fi

# Marker selection logs
MARKERS_LOG="${LOGS_DIR}/marker_selection_execution.log"
if [ -f "$MARKERS_LOG" ]; then
    echo "Marker selection stage: Log found"
    MARKERS_LINES=$(wc -l < "$MARKERS_LOG")
    echo "  - Log lines: $MARKERS_LINES"
    if [ $MARKERS_LINES -gt 0 ]; then
        echo "  - Last line: $(tail -1 "$MARKERS_LOG")"
    fi
else
    echo "Marker selection stage: No log found"
fi

echo ""

# Check for error files
echo "=== Error Check ==="
ERROR_FILES=$(find "$LOGS_DIR" -name "*.err" -size +0 2>/dev/null)
if [ -n "$ERROR_FILES" ]; then
    echo "Warning: Non-empty error files found:"
    echo "$ERROR_FILES"
    echo ""
    echo "Check these files for potential issues:"
    for error_file in $ERROR_FILES; do
        echo "  $error_file ($(wc -l < "$error_file") lines)"
    done
else
    echo "No error files with content found."
fi

echo ""
echo "=== Monitor Complete ==="
echo "For continuous monitoring, run: watch -n 30 $0 $LOGS_DIR" 