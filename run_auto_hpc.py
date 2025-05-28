from sys import argv
import os
from time import sleep
from datetime import datetime

def wait_completition(log_folder):
    path = 'logs/' + log_folder
    file_count = 0

    while file_count != 24:
        file_count = len([f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))])
        sleep(40)

def run_serial(input_file):
    cmd = f"./run_serial.sh {input_file}"

    os.system(cmd)

    time = datetime.now().strftime("%H:%M")
    print(f"{time} Running SERIAL. Waiting completition...")

def run_mpi(num_processes, input_file, log_folder):
    cmd = f"./run_mpi_hpc.sh {num_processes} {input_file} {log_folder}"

    os.system(cmd)

    time = datetime.now().strftime("%H:%M")
    print(f"{time} Running MPI with {num_processes}. Waiting completition...")

def run_omp(num_processes, input_file, log_folder):
    cmd = f"./run_omp_hpc.sh {num_processes} {input_file} {log_folder}"

    os.system(cmd)
    time = datetime.now().strftime("%H:%M")
    print(f"{time} Running OMP with {num_processes}. Waiting completition...")

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
    time = datetime.now().strftime("%d_%m_%Y@%H_%M")
    for i in range(0, run_number):
        log_folder=f"{time}/{i}_run"
        while num_processes<=64:
            if mode == "mpi" or mode == "all":
                run_mpi(num_processes, input_file, log_folder)

            if mode == "omp" or mode == "all":
                run_omp(num_processes, input_file, log_folder)
                
        num_processes*=2

        wait_completition(log_folder)
 

    run_serial(input_file)   

if __name__ == "__main__":
    if len(argv) < 3:
        print("Usage: python3 run_auto.py <[mpi, omp, all]> <input_file> <runs_number>")
        exit(1)

    run_script()