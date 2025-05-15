import glob
import os
import sys

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

LOG_PATH = "logs/results.log"
PLOT_DIR = "logs/plots"
PLOT_FILE = "combined_plot.png"


def plot_results():
    df = pd.read_csv(LOG_PATH, sep=r"\s+")
    _plot_dataframe(df)


def read_base_time(serial_file):
    try:
        with open(serial_file, "r") as f:
            line = f.readline().strip()
            if line:
                parts = line.split()
                if len(parts) == 4:
                    _, _, _, time = parts
                    return float(time)
    except FileNotFoundError:
        print(f"Error: Base serial file '{serial_file}' not found.")
    except Exception as e:
        print(f"Error reading base time: {e}")
    return None


def plot_from_output_files(log_dir):
    serial_file = os.path.join(log_dir, "serial_parallel_mst.o1")
    T1 = read_base_time(serial_file)

    if T1 is None:
        print("Cannot calculate speedup/efficiency: base time not available.")
        return

    patterns = [
        ("mpi", os.path.join(log_dir, "mpi_parallel_mst.o*")),
        ("omp", os.path.join(log_dir, "omp_parallel_mst.o*")),
    ]
    rows = []

    for impl_type, pattern in patterns:
        files = glob.glob(pattern)

        for file in files:
            print(f"Processing file: {file}")
            with open(file, "r") as f:
                line = f.readline().strip()
                if line:
                    parts = line.split()
                    if len(parts) == 4:
                        algo, file_name, num_processes, time = parts
                        time = float(time)
                        num_processes = int(num_processes)
                        speedup = T1 / time
                        efficiency = speedup / num_processes
                        rows.append(
                            {
                                "implementation": impl_type,
                                "algorithm": algo,
                                "file_name": file_name,
                                "num_processes": num_processes,
                                "Time": time,
                                "Speedup": speedup,
                                "Efficiency": efficiency,
                            }
                        )

    if not rows:
        print("No valid data found in output files.")
        return

    df = pd.DataFrame(rows)
    _plot_dataframe(df, log_dir)


def _plot_dataframe(df: pd.DataFrame, log_dir: str):
    os.makedirs(os.path.join(log_dir, "plots"), exist_ok=True)

    sns.set(style="whitegrid")

    # Plot: Time
    plt.figure(figsize=(12, 7))
    sns.lineplot(
        data=df,
        x="num_processes",
        y="Time",
        hue="file_name",
        style="implementation",
        markers=True,
        dashes=False,
    )
    plt.title("Performance Comparison by Input File and Implementation")
    plt.xlabel("Number of Processes")
    plt.ylabel("Time (s)")
    plt.legend(
        title="File / Implementation", bbox_to_anchor=(1.05, 1), loc="upper left"
    )
    plt.tight_layout()
    plt.savefig(os.path.join(log_dir, "plots", PLOT_FILE))
    plt.close()

    # Plot: Speedup
    plt.figure(figsize=(12, 7))
    sns.lineplot(
        data=df,
        x="num_processes",
        y="Speedup",
        hue="file_name",
        style="implementation",
        markers=True,
        dashes=False,
    )
    plt.title("Speedup by Input File and Implementation")
    plt.xlabel("Number of Processes")
    plt.ylabel("Speedup")
    plt.tight_layout()
    plt.savefig(os.path.join(log_dir, "plots", "speedup_plot.png"))
    plt.close()

    # Plot: Efficiency
    plt.figure(figsize=(12, 7))
    sns.lineplot(
        data=df,
        x="num_processes",
        y="Efficiency",
        hue="file_name",
        style="implementation",
        markers=True,
        dashes=False,
    )
    plt.title("Efficiency by Input File and Implementation")
    plt.xlabel("Number of Processes")
    plt.ylabel("Efficiency")
    plt.tight_layout()
    plt.savefig(os.path.join(log_dir, "plots", "efficiency_plot.png"))
    plt.close()

    # Save CSV
    df.to_csv(os.path.join(log_dir, "plots", "performance_metrics.csv"), index=False)


if __name__ == "__main__":
    if len(sys.argv) == 0:
        print("Usage: python3 plot_results.py [--local] [--dir <log_dir>]")
        sys.exit(1)

    if "--local" in sys.argv:
        plot_results()
    else:
        try:
            dir_index = sys.argv.index("--dir")
            log_dir = sys.argv[dir_index + 1]
        except (ValueError, IndexError):
            log_dir = "logs"  # default fallback
        plot_from_output_files(log_dir)

    print(f"Plots saved in '{log_dir}'")
    print(f"Combined plot saved as '{PLOT_FILE}'")
