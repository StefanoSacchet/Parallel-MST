#!/bin/bash

# Check if input file is passed
if [ $# -lt 2 ]; then
    echo "Usage: $0 <input_file> <output_name> <optional_log_folder>"
    exit 1
fi

input_file="$1"
output_name="$2"
log_folder="logs"

if [ -z "$3" ]; then
    log_folder="logs/"
    echo "Using default log folder: '$log_folder'"
else
    # Remove any trailing slash from log_folder
    log_folder="${log_folder%/}"
    # Remove any leading/trailing slashes from input
    input="${3#/}"
    input="${input%/}"
    
    log_folder="$log_folder/$input/"
    echo "Using log folder: $log_folder"
fi

mkdir -p $log_folder

source load_modules.sh
echo "Building release SERIAL..."
# make clean
make release-hpc RUN_TYPE=SERIAL

# Create a temporary PBS script
job_script=$(mktemp)

cat <<EOF > "$job_script"
#!/bin/bash
#PBS -l select=1:ncpus=1:mem=128gb
#PBS -l place=pack:excl
#PBS -l walltime=01:00:00
#PBS -q short_cpuQ
#PBS -N ser_${output_name}
#PBS -o ${log_folder}serial_${output_name}.o1
#PBS -e ${log_folder}serial_${output_name}.e1
${PWD}/build/bin/serial_mst "$input_file"
EOF

qsub "$job_script"
