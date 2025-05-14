#!/bin/bash
# This script runs the MPI program with 1 to 10 processes for a given input file

# Check if input file is provided
if [ $# -lt 1 ]; then
    echo "Usage: $0 <input_file>"
    exit 1
fi

input_file="$1"

# Loop over number of processes from 1 to 10
for num_processes in $(seq 1 10); do
    echo "Running with $num_processes process(es)..."
    mpiexec -n "$num_processes" build/bin/parallel_mst "$input_file"
    echo "--------------------------------------------------"
done
