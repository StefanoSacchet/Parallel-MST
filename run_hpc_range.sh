#!/bin/bash

# Check if input file is passed
if [ $# -lt 1 ]; then
    echo "Usage: $0 <input_file>"
    exit 1
fi

input_file="$1"

for ((p=2; p<=128; p*=2)); do
    # Create a temporary PBS script
    job_script=$(mktemp)

    cat <<EOF > "$job_script"
#!/bin/bash
#PBS -l select=1:ncpus=$p:mem=2gb
#PBS -l walltime=00:01:00
#PBS -q short_cpuQ
#PBS -N parallel_mst_${p}
#PBS -o logs/parallel_mst.o${p}
#PBS -e logs/parallel_mst.e${p}

module load mpich-3.2
mpirun.actual -n $p ${PWD}/build/bin/parallel_mst "$input_file"
EOF

    echo "Submitting job with $p processes..."
    qsub "$job_script"
done
