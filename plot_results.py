import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

LOG_PATH = "logs/results.log"
PLOT_DIR = "logs/plots"
PLOT_FILE = "combined_plot.png"


def plot_results():
    # Read the log file
    df = pd.read_csv(LOG_PATH, sep=r"\s+")

    # Group by file_name and num_processes, and average the Time
    avg_df = df.groupby(["file_name", "num_processes"], as_index=False).mean()

    # Make sure plots/ directory exists
    os.makedirs(PLOT_DIR, exist_ok=True)

    # Set a style for prettier plots
    sns.set(style="whitegrid")

    # Create a single plot with one line per file_name
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=avg_df, x="num_processes", y="Time", hue="file_name", marker="o")

    plt.title("Performance Comparison by Input File")
    plt.xlabel("Number of Processes")
    plt.ylabel("Time (s)")
    plt.legend(title="Input File")
    plt.tight_layout()

    # Save the plot
    plt.savefig(os.path.join(PLOT_DIR, PLOT_FILE))
    plt.close()


if __name__ == "__main__":
    plot_results()
    print(f"Plots saved in '{PLOT_DIR}'")
