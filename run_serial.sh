#!/bin/bash

# Check if input file is passed
if [ $# -lt 1 ]; then
    echo "Usage: $0 <input_file>"
    exit 1
fi

input_file="$1"
mkdir -p logs/

source load_modules.sh
echo "Building release SERIAL..."
make clean
make release-hpc RUN_TYPE=SERIAL

# Create a temporary PBS script
job_script=$(mktemp)

cat <<EOF > "$job_script"
#!/bin/bash
#PBS -l select=1:ncpus=1:mem=64gb
#PBS -l walltime=00:20:00
#PBS -q short_cpuQ
#PBS -N parallel_mst
#PBS -o logs/serial_parallel_mst.o1
#PBS -e logs/serial_parallel_mst.e1
${PWD}/build/bin/parallel_mst "$input_file"
EOF

qsub "$job_script"
