from sys import argv
import os
from time import sleep
from datetime import datetime

def wait_completition(log_folder, file_path):
    path = log_folder + '/' + file_path
    while not os.path.exists(path):
        sleep(20)

def run_mpi(num_processes, input_file, log_folder):
    cmd = f"./run_mpi_hpc.sh {num_processes} {input_file} {log_folder}"
    file_path=f"mpi_parallel_mst.o{num_processes}"

    os.system(cmd)
    print(f"Running MPI with {num_processes}. Waiting completition...")

    wait_completition(log_folder, file_path)

def run_omp(num_processes, input_file, log_folder):
    cmd = f"./run_omp_hpc.sh {num_processes} {input_file} {log_folder}"
    file_path=f"omp_parallel_mst.o{num_processes}"

    os.system(cmd)
    print(f"Running OMP with {num_processes}. Waiting completition...")

    wait_completition(log_folder, file_path) 

def run_all(num_processes, input_file, log_folder):
    run_mpi(num_processes, input_file, log_folder)
    run_omp(num_processes, input_file, log_folder)

def run_script():
    if argv[1] not in ["mpi", "omp", "all"]:
        print("Found non existing mode. Use 'mpi', 'omp' or 'all'")
        exit(1)

    run_number=1
    if len(argv) == 4:
        run_number=int(argv[3])

    mode = argv[1]
    input_file = argv[2]

    num_processes = 2
    for i in range(0, run_number):
        time = datetime.now().strftime("%d_%m_%Y@%H_%M")
        log_folder=f"{time}/{i}_run"
        while num_processes<=64:
            # run script
            if mode == "mpi":
                run_mpi(num_processes, input_file, log_folder)
            elif mode == "omp":
                run_omp(num_processes, input_file, log_folder)
            elif mode == "all":
                run_all(num_processes, input_file, log_folder)
                
            num_processes*=2    

if __name__ == "__main__":
    if len(argv) < 3:
        print("Usage: python3 run_auto.py <[mpi, omp]> <input_file> <runs_number>")
        exit(1)

    run_script()