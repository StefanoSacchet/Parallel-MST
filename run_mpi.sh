#!/bin/bash
# This script runs the mpi program with number of preocesses passed as input

# Check if a parameter is passed
if [ -z "$1" ]; then
    echo "Usage: $0 <parameter>"
    exit 1
fi

input_param="$1"

mpiexec -n $input_param build/debug/bin/parallel_mst
