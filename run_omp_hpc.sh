#!/bin/bash
# This script runs the OMP program on HPC with number of preocesses passed as input

# Check if a parameter is passed
if [ $# -lt 2 ]; then
    echo "Usage: $0 <num_processes> <input_file> <optional_log_folder>"
    exit 1
fi

num_processes="$1"
input_file="$2"
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
echo "Building release OMP..."
make clean
make release-hpc RUN_TYPE=OMP

# Create a temporary PBS script
job_script=$(mktemp)

cat <<EOF > "$job_script"
#!/bin/bash
#PBS -l select=1:ncpus=$num_processes:mem=64gb
#PBS -l walltime=00:20:00
#PBS -q short_cpuQ
#PBS -N parallel_mst_${num_processes}
#PBS -o ${log_folder}omp_parallel_mst.o${num_processes}
#PBS -e ${log_folder}omp_parallel_mst.e${num_processes}
${PWD}/build/bin/pomp_mst "$input_file"
EOF

qsub "$job_script"
