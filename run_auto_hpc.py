from sys import argv
import os
from time import sleep
from datetime import datetime

def wait_completition(log_folder, file_count):
    path = 'logs/' + log_folder
    current_files = len([f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))])
    wait_file = file_count + current_files

    while current_files < wait_file:
        current_files = len([f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))])
        print(f"Found {current_files} files. Needs to reach ${wait_file}")
        sleep(40)

def run_serial(input_file):
    cmd = f"./run_serial.sh {input_file}"

    os.system(cmd)

    time = datetime.now().strftime("%H:%M")
    print(f"{time} Running SERIAL. Waiting completition...")

def run_mpi(num_processes, input_file, place, log_folder):
    cmd = f"./run_mpi_hpc.sh {num_processes} {input_file} {place} {log_folder}"

    os.system(cmd)

    time = datetime.now().strftime("%H:%M")
    print(f"{time} Running MPI with {num_processes}. Waiting completition...")

def run_omp(num_processes, input_file, place, log_folder):
    cmd = f"./run_omp_hpc.sh {num_processes} {input_file} {place} {log_folder}"

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
    for place in ["pack", "scatter"]:
        for i in range(0, run_number):
            log_folder=f"{time}/{i}_run"
            file_count=0
            while num_processes<=64:
                if mode == "mpi" or mode == "all":
                    run_mpi(num_processes, input_file, place, log_folder)
                    file_count+=2

                if mode == "omp" or mode == "all":
                    run_omp(num_processes, input_file, place, log_folder)
                    file_count+=2
                
                sleep(2)
                    
            num_processes*=2

            wait_completition(log_folder, file_count)
 
    run_serial(input_file)   

if __name__ == "__main__":
    if len(argv) < 3:
        print("Usage: python3 run_auto.py <[mpi, omp, all]> <input_file> <runs_number>")
        exit(1)

    run_script()