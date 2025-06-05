import argparse
import os
from time import sleep

def run_mpi(n_cores, input_file, cpus, place, log_folder):
    cmd = f"./run_mpi_hpc.sh {n_cores} {input_file} {cpus} {place} {log_folder}"

    os.system(cmd)

    print(f"Running MPI with {n_cores}_{place}.")

def run_omp(n_cores, input_file, cpus, place, log_folder):
    cmd = f"./run_omp_hpc.sh {n_cores} {input_file} {cpus} {place} {log_folder}"

    os.system(cmd)
    print(f"Running OMP with {n_cores}_{place}")

def run_hybrid(n_cores, input_file, cpus, place, log_folder):
    cmd = f"./run_hybrid_hpc.sh {n_cores} {input_file} {cpus} {place} {log_folder}"

    os.system(cmd)
    print(f"Running HYBRID with {n_cores}_{place}")

def run_script(mode, input_files):
    n_cores = 1

    for input_file in input_files:
        path = "./dataset/"+input_file
        if not os.path.isfile(path):
            print(f"File not exists at '{path}'. Skipped.")
            continue
        
        print(f"Using file at '{path}'.")
        
        log_folder="weak_scalability"+os.path.splitext(os.path.basename(input_file))[0]
        
        if mode == "mpi" or mode == "all":
            run_mpi(n_cores, input_file, 1, "pack", log_folder)
            sleep(20)

        if mode == "omp" or mode == "all":
            run_omp(n_cores, input_file, 1, "pack", log_folder)
            sleep(20)

        if mode == "hybrid" or mode == "all":
            run_hybrid(n_cores, input_file, 1, "pack", log_folder)
            sleep(20)

        n_cores*=2

    print("---- AUTO RUN SCRIPT TERMINATED ----")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run benchmark weak scalability.")
    parser.add_argument("mode", choices=["mpi", "omp", "hybrid", "all"], help="Execution mode")
    parser.add_argument("--input", nargs="+", help="Input file(s)", required=True)

    args = parser.parse_args()

    run_script(args.mode, args.input)