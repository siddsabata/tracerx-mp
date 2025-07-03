#!/usr/bin/env bash
# install_environments.sh
# This script iterates over all *.yml files in the environments/ directory and
# creates conda environments for each. Use --force to recreate existing envs.

set -euo pipefail

ENV_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )/environments"
FORCE=""

# Parse optional flags
for arg in "$@"; do
  case $arg in
    --force)
      FORCE="--force"
      shift
      ;;
    *)
      echo "Unknown argument: $arg"
      echo "Usage: $0 [--force]"
      exit 1
      ;;
  esac
 done

if ! command -v conda &> /dev/null; then
  echo "Error: 'conda' command not found. Please install Miniconda or Anaconda first." >&2
  exit 1
fi

echo "Installing conda environments from $ENV_DIR..."

for env_file in "$ENV_DIR"/*.yml; do
  [ -e "$env_file" ] || { echo "No .yml files found in $ENV_DIR"; exit 1; }

  env_name=$(basename "$env_file" | sed 's/_env\.yml$//' | sed 's/\.yml$//')
  echo "Creating environment '$env_name' from $env_file..."
  conda env create $FORCE -n "$env_name" -f "$env_file"
  echo "Environment '$env_name' created."
  echo "----------------------------------------"
 done

echo "All environments installed successfully."