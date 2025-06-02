from sys import argv
import os
from time import sleep, time
from datetime import datetime

PID = os.getpid()

def count_files(path):
    return len([f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))])

def wait_completition(log_folder, file_count):
    path = 'logs/' + log_folder
    start_time = time()
    timeout = 15 * 60  # 15 minutes in seconds

    current_files = count_files(path)
    wait_file = file_count + current_files

    while current_files < wait_file:
        elapsed_time = time() - start_time
        if elapsed_time > timeout:
            print("Timeout reached after 15 minutes.")
            break

        current_files = count_files(path)
        print(f"Found {current_files} files. Needs to reach {wait_file}.")
        print(f"To kill PID: {PID}")
        sleep(60)

def run_serial(input_file):
    cmd = f"./run_serial.sh {input_file}"

    os.system(cmd)

    time = datetime.now().strftime("%H:%M")
    print(f"{time} Running SERIAL. ")

def run_mpi(n_cores, input_file, cpus, place, log_folder):
    cmd = f"./run_mpi_hpc.sh {n_cores} {input_file} {cpus} {place} {log_folder}"

    os.system(cmd)

    time = datetime.now().strftime("%H:%M")
    print(f"{time} Running MPI with {n_cores}_{place}.")

def run_omp(n_cores, input_file, cpus, place, log_folder):
    cmd = f"./run_omp_hpc.sh {n_cores} {input_file} {cpus} {place} {log_folder}"

    os.system(cmd)
    time = datetime.now().strftime("%H:%M")
    print(f"{time} Running OMP with {n_cores}_{place}")

def run_hybrid(n_cores, input_file, cpus, place, log_folder):
    cmd = f"./run_hybrid_hpc.sh {n_cores} {input_file} {cpus} {place} {log_folder}"

    os.system(cmd)
    time = datetime.now().strftime("%H:%M")
    print(f"{time} Running HYBRID with {n_cores}_{place}")

def submit_jobs(time, mode, input_file, cpus, place, n_run, max_cores):
    for i in range(0, n_run):
        log_folder=f"{time}/{cpus}_cpu/{place}/{i}_run"
        file_count=0
        n_cores = 1
        while n_cores<=max_cores:
            if mode == "mpi" or mode == "all":
                run_mpi(n_cores, input_file, cpus, place, log_folder)
                file_count+=2
                sleep(20)

            if mode == "omp" or mode == "all":
                run_omp(n_cores, input_file, cpus, place, log_folder)
                file_count+=2
                sleep(20)

            if mode == "hybrid" or mode == "all":
                run_hybrid(n_cores, input_file, cpus, place, log_folder)
                file_count+=2
                sleep(20)
            
            n_cores*=2

        print(f"Submitted {file_count/2} jobs with {place}. Waiting for completition.")
        wait_completition(log_folder, file_count)

def run_script():
    if argv[1] not in ["mpi", "omp", "hybrid", "all"]:
        print("Found non existing mode. Use 'mpi', 'omp', 'hybrid' or 'all'")
        exit(1)

    n_run=1
    if len(argv) == 4:
        n_run=int(argv[3])

    mode = argv[1]
    input_file = argv[2]

    time = datetime.now().strftime("%d_%m_%Y@%H_%M")

    # 1 CPU with cores from 2 to 64 using pack
    submit_jobs(time, mode, input_file, 1, "pack", n_run, 64)
    # 2 CPUs with cores from 2 to 32 using pack and scatter
    submit_jobs(time, mode, input_file, 2, "pack", n_run, 32)
    submit_jobs(time, mode, input_file, 2, "scatter", n_run, 32)
    # 4 CPUs with cores from 2 to 32 using pack and scatter
    submit_jobs(time, mode, input_file, 4, "pack", n_run, 16)
    submit_jobs(time, mode, input_file, 4, "scatter", n_run, 16)
    
    run_serial(input_file)   

if __name__ == "__main__":
    if len(argv) < 3:
        print("Usage: python3 run_auto.py <[mpi, omp, hybrid, all]> <input_file> <runs_number>")
        exit(1)

    run_script()