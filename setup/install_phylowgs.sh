#!/bin/bash

# TracerX PhyloWGS Installation Script
# Installs PhyloWGS to the src/phylowgs directory

# Get script directory for absolute paths
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
TRACERX_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Installing PhyloWGS for TracerX Pipeline..."
echo "TracerX root directory: $TRACERX_ROOT"

# Create logs directory
mkdir -p "$TRACERX_ROOT/logs"

# Install PhyloWGS to src/phylowgs/
cd "$TRACERX_ROOT/src/phylowgs"

if [ -d "phylowgs" ]; then
    echo "PhyloWGS directory already exists. Removing old installation..."
    rm -rf phylowgs
fi

echo "Cloning PhyloWGS repository..."
git clone https://github.com/morrislab/phylowgs.git

cd phylowgs
echo "Repository cloned; compiling PhyloWGS..."

# Compile PhyloWGS
g++ -o mh.o -O3 mh.cpp util.cpp `gsl-config --cflags --libs`

if [ $? -eq 0 ]; then
    echo "PhyloWGS successfully installed to src/phylowgs/phylowgs/"
    echo "Installation complete!"
else
    echo "Error: PhyloWGS compilation failed!"
    echo "Please ensure you have g++ and GSL development libraries installed:"
    echo "  Ubuntu/Debian: sudo apt-get install build-essential libgsl-dev"
    echo "  CentOS/RHEL: sudo yum groupinstall 'Development Tools' && sudo yum install gsl-devel"
    exit 1
fi