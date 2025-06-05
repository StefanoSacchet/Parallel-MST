#!/bin/bash

# THIS SCRIPT GENERATES GRAPHS OF INCREMENTAL SIZE USING HPC CLUSTER
# VERTICES: 25K
# EDGES: 200K UP TO 1.6M

vertices=25000
edges=200000

mkdir -p "dataset/generated/"

source load_modules.sh
make release RUN_TYPE=GRAPH_GEN

generate_and_submit_pbs_script() {
    local V="$1"
    local E="$2"

    # Format vertex and edge labels (e.g., 25000 → 25k)
    local Vk=$((V / 1000))k
    local Ek=$((E / 1000))k

    source load_modules.sh
    job_script=$(mktemp)

    cat <<EOF > "$job_script"
#!/bin/bash
#PBS -l select=1:ncpus=32:mem=64gb 
#PBS -l walltime=00:20:00
#PBS -q short_cpuQ
#PBS -N gen_graph_${Vk}_${Ek}
#PBS -o dataset/generated/${Vk}${Ek}.txt
#PBS -e dataset/generated/${Vk}${Ek}.err

${PWD}/build/bin/graph_generator $V $E
EOF

    echo "Submitting job: V=$V, E=$E → Output: ${Vk}${Ek}.txt"  
    qsub "$job_script"
}


for ((p=0; p<=3; p+=1)); do
    generate_and_submit_pbs_script $vertices $edges
    edges=$((edges * 2))
done
