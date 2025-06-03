import os
from time import sleep, time
from datetime import datetime
import argparse

PID = os.getpid()

def count_files(path):
    return len([f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))])

def wait_completition(log_folder, file_count):
    path = 'logs/' + log_folder
    start_time = time()
    timeout = 15 * 60  # 15 minutes in seconds

    current_files = count_files(path)

    while current_files < file_count:
        elapsed_time = time() - start_time
        if elapsed_time > timeout:
            print("Timeout reached after 15 minutes.")
            break

        current_files = count_files(path)
        print(f"Found {current_files} files. Needs to reach {file_count}.")
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

DEFAULT_INPUT_FILES = ["generated/1k25k.txt", "generated/1k310k.txt", "generated/80k65m.txt", "generated/80k2b.txt", "generated/500k1b.txt"] 

def run_script(mode, input_files, n_run):

    for input_file in input_files:
        path = "./dataset/"+input_file
        if not os.path.isfile(path):
            print(f"File not exists at '{path}'. Skipped.")
            continue
        
        print(f"Using file at '{path}'.")

        time = datetime.now().strftime("%d_%m_%Y@%H_%M")
        # 1 CPU with cores from 2 to 64 using pack
        submit_jobs(time, mode, input_file, 1, "pack", n_run, 64)
        # 2 CPUs with cores from 2 to 32 using pack and scatter
        submit_jobs(time, mode, input_file, 2, "pack", n_run, 32)
        submit_jobs(time, mode, input_file, 2, "scatter", n_run, 32)
        # 4 CPUs with cores from 2 to 32 using pack and scatter
        submit_jobs(time, mode, input_file, 4, "pack", n_run, 16)
        submit_jobs(time, mode, input_file, 4, "scatter", n_run, 16)

        # run_serial(input_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run benchmark automation.")
    parser.add_argument("mode", choices=["mpi", "omp", "hybrid", "all"], help="Execution mode")
    parser.add_argument("--input", nargs="+", default=DEFAULT_INPUT_FILES, help="Input file(s)")
    parser.add_argument("--runs", type=int, default=1, help="Number of runs")

    args = parser.parse_args()

    run_script(args.mode, args.input, args.runs)