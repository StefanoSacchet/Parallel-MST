#!/bin/bash
# This script runs the mpi program on hpc with number of preocesses passed as input

# Check if a parameter is passed
if [ $# -lt 4 ]; then
    echo "Usage: $0 <num_processes> <input_file> <cpus> <placement> <log_folder>"
    echo "Placement options: [pack, scatter]."
    exit 1
fi

num_processes="$1"
input_file="$2"
cpus="$3"
placement="$4"
log_folder="logs"

if [ "$placement" != "pack" ] && [ "$placement" != "scatter" ]; then
    echo "Found not allowed placement: ${placement}. Use 'pack' or 'scatter'."
    exit 1 
fi

if [ -z "$5" ]; then
    log_folder="logs/"
    echo "Using default log folder: '$log_folder'"
else
    # Remove any trailing slash from log_folder
    log_folder="${log_folder%/}"
    # Remove any leading/trailing slashes from input
    input="${5#/}"
    input="${input%/}"
    
    log_folder="$log_folder/$input/"
    echo "Using log folder: $log_folder"
fi

mkdir -p $log_folder
source load_modules.sh
echo "Building release MPI..."
make clean
make release-hpc RUN_TYPE=MPI

# Create a temporary PBS script
job_script=$(mktemp)

cat <<EOF > "$job_script"
#!/bin/bash
#PBS -l select=${cpus}:ncpus=$num_processes:mem=64gb 
#PBS -l place=${placement}:excl
#PBS -l walltime=00:20:00
#PBS -q short_cpuQ
#PBS -N mpi_mst${num_processes}_${placement}
#PBS -o ${log_folder}mpi_parallel_mst_${placement}.o$((num_processes*cpus))
#PBS -e ${log_folder}mpi_parallel_mst_${placement}.e$((num_processes*cpus))
module load mpich-3.2
mpirun.actual -n $num_processes ${PWD}/build/bin/mpi_mst "$input_file"
EOF

qsub "$job_script"
