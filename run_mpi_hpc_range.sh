#!/bin/bash

# Check if input file is passed
if [ $# -lt 1 ]; then
    echo "Usage: $0 <input_file>"
    exit 1
fi

input_file="$1"
mkdir -p logs/

generate_and_submit_pbs_script() {
    local select_nodes="$1"
    local ncpus="$2"
    local mem="$3"

    # Create a temporary PBS script
    job_script=$(mktemp)

    cat <<EOF > "$job_script"
#!/bin/bash
#PBS -l select=${select_nodes}:ncpus=${ncpus}:mem=${mem}
#PBS -l walltime=00:10:00
#PBS -q short_cpuQ
#PBS -N parallel_mst_${ncpus}
#PBS -o logs/mpi_parallel_mst.o${ncpus}
#PBS -e logs/mpi_parallel_mst.e${ncpus}

module load mpich-3.2
mpirun.actual -n ${ncpus} ${PWD}/build/bin/parallel_mst "$input_file"
EOF

    echo "Submitting job with $ncpus processes on $select_nodes node(s)..."
    qsub "$job_script"
}

for ((p=2; p<=64; p*=2)); do
  generate_and_submit_pbs_script 1 "$p" 32gb
done

generate_and_submit_pbs_script 2 64 32gb
