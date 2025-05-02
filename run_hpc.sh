#!/bin/bash
# This script runs the mpi program with number of preocesses passed as input

# Check if a parameter is passed
if [ $# -lt 2 ]; then
    echo "Usage: $0 <num_processes> <input_file>>"
    exit 1
fi

num_processes="$1"
input_file="$2"

# Create a temporary PBS script
job_script=$(mktemp)

cat <<EOF > "$job_script"
#!/bin/bash
#PBS -l select=1:ncpus=$num_processes:mem=2gb
#PBS -l walltime=00:01:00
#PBS -q short_cpuQ
#PBS -N parallel_mst
module load mpich-3.2
mpirun.actual -n $num_processes ${PWD}/build/bin/parallel_mst "$input_file"
EOF

qsub "$job_script"
