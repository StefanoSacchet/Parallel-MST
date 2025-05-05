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


def plot_from_output_files():
    files = glob.glob("parallel_mst.o*")
    rows = []

    for file in files:
        print(f"Processing file: {file}")
        with open(file, "r") as f:
            line = f.readline().strip()
            if line:
                parts = line.split()
                if len(parts) == 4:
                    algo, file_name, num_processes, time = parts
                    rows.append(
                        {
                            "algorithm": algo,
                            "file_name": file_name,
                            "num_processes": int(num_processes),
                            "Time": float(time),
                        }
                    )

    if not rows:
        print("No valid data found in output files.")
        return

    df = pd.DataFrame(rows)
    _plot_dataframe(df)


def _plot_dataframe(df: pd.DataFrame):
    os.makedirs(PLOT_DIR, exist_ok=True)

    # Only average numeric column (Time)
    avg_df = df.groupby(["file_name", "num_processes"], as_index=False)["Time"].mean()

    sns.set(style="whitegrid")

    # Combined plot
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=avg_df, x="num_processes", y="Time", hue="file_name", marker="o")
    plt.title("Performance Comparison by Input File")
    plt.xlabel("Number of Processes")
    plt.ylabel("Time (s)")
    plt.legend(title="Input File")
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, PLOT_FILE))
    plt.close()

    # Individual plots
    for file_name in avg_df["file_name"].unique():
        subset = avg_df[avg_df["file_name"] == file_name]
        plt.figure(figsize=(8, 5))
        sns.lineplot(data=subset, x="num_processes", y="Time", marker="o")
        plt.title(f"Performance for {file_name}")
        plt.xlabel("Number of Processes")
        plt.ylabel("Time (s)")
        plt.tight_layout()
        sanitized_name = os.path.basename(file_name).replace("/", "__")
        plt.savefig(os.path.join(PLOT_DIR, f"{sanitized_name}.png"))
        plt.close()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--hpc":
        plot_from_output_files()
    else:
        plot_results()

    print(f"Plots saved in '{PLOT_DIR}'")
    print(f"Combined plot saved as '{PLOT_FILE}'")
