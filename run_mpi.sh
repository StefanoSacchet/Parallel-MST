#!/bin/bash
# This script runs the mpi program with number of preocesses passed as input

# Check if a parameter is passed
if [ $# -lt 2 ]; then
    echo "Usage: $0 <num_processes> <input_file>>"
    exit 1
fi

num_processes="$1"
input_file="$2"

mpiexec -n "$num_processes" build/debug/bin/parallel_mst "$input_file"

