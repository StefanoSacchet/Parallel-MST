import glob
import os
import sys
from collections import defaultdict

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


def find_data_folders(base_dir, specific_folders=None):
    """Find data@time folders in the base directory."""
    data_folders = []
    
    if specific_folders:
        # Use specific folders provided by user
        for folder_name in specific_folders:
            # Handle both full path and just folder name
            if os.path.isabs(folder_name):
                folder_path = folder_name
            else:
                folder_path = os.path.join(base_dir, folder_name)
            
            if os.path.isdir(folder_path):
                data_folders.append(folder_path)
            else:
                print(f"Warning: Folder '{folder_path}' not found or not a directory")
    else:
        # Auto-discover all data@time folders
        for item in os.listdir(base_dir):
            item_path = os.path.join(base_dir, item)
            if os.path.isdir(item_path) and ('@' in item):  # More flexible pattern matching
                data_folders.append(item_path)
    
    return sorted(data_folders)


def get_run_folders(data_folder):
    """Get all run folders (0_run, 1_run, ..., n_run) from a data folder."""
    run_folders = []
    for item in os.listdir(data_folder):
        item_path = os.path.join(data_folder, item)
        if os.path.isdir(item_path) and item.endswith('_run'):
            run_folders.append(item_path)
    return sorted(run_folders)


def read_file_data(file_path):
    """Read data from a single output file."""
    try:
        with open(file_path, "r") as f:
            line = f.readline().strip()
            if line:
                parts = line.split()
                if len(parts) == 4:
                    algo, file_name, num_processes, time = parts
                    return {
                        'algorithm': algo,
                        'file_name': file_name,
                        'num_processes': int(num_processes),
                        'time': float(time)
                    }
    except (FileNotFoundError, ValueError, IndexError) as e:
        print(f"Error reading file {file_path}: {e}")
    return None


def collect_all_data(base_dir, specific_folders=None):
    """Collect data from all folders and find minimum times for each configuration."""
    # Structure: [data_folder][impl_type][file_pattern][run_folder] = data
    all_data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    
    data_folders = find_data_folders(base_dir, specific_folders)
    if not data_folders:
        if specific_folders:
            print(f"None of the specified folders found: {specific_folders}")
        else:
            print(f"No date@time folders found in {base_dir}")
        return None
    
    print(f"Found {len(data_folders)} data folders: {[os.path.basename(f) for f in data_folders]}")
    
    for data_folder in data_folders:
        run_folders = get_run_folders(data_folder)
        if not run_folders:
            print(f"No run folders found in {data_folder}")
            continue
            
        print(f"Processing {len(run_folders)} run folders in {os.path.basename(data_folder)}")
        
        patterns = [
            ("mpi", "mpi_parallel_mst.o*"),
            ("omp", "omp_parallel_mst.o*"),
            ("serial", "serial_parallel_mst.o*")
        ]
        
        for run_folder in run_folders:
            for impl_type, pattern in patterns:
                files = glob.glob(os.path.join(run_folder, pattern))
                for file_path in files:
                    data = read_file_data(file_path)
                    if data:
                        # Create a unique key for this configuration
                        config_key = (data['algorithm'], data['file_name'], data['num_processes'])
                        all_data[data_folder][impl_type][config_key].append(data)
    
    return all_data


def get_minimum_times(all_data):
    """Get minimum times for each configuration across all runs."""
    min_data = []
    
    for data_folder, impl_data in all_data.items():
        folder_name = os.path.basename(data_folder)
        
        # First, find the serial base time for this data folder
        T1 = None
        if 'serial' in impl_data:
            for config_key, runs in impl_data['serial'].items():
                if runs:  # If we have serial data
                    min_time = min(run['time'] for run in runs)
                    T1 = min_time
                    break
        
        if T1 is None:
            print(f"Warning: No serial time found for {folder_name}, using first available time as baseline")
            # Find any available time as baseline
            for impl_type, configs in impl_data.items():
                for config_key, runs in configs.items():
                    if runs:
                        T1 = min(run['time'] for run in runs)
                        break
                if T1:
                    break
        
        if T1 is None:
            print(f"Warning: No baseline time found for {folder_name}, skipping")
            continue
        
        for impl_type, configs in impl_data.items():
            if impl_type == 'serial':
                continue  # Skip serial for plotting (already used for baseline)
                
            for config_key, runs in configs.items():
                if not runs:
                    continue
                    
                # Find minimum time across all runs
                min_time = min(run['time'] for run in runs)
                best_run = min(runs, key=lambda x: x['time'])
                
                speedup = T1 / min_time
                efficiency = speedup / best_run['num_processes']
                
                min_data.append({
                    'data_folder': folder_name,
                    'implementation': impl_type,
                    'algorithm': best_run['algorithm'],
                    'file_name': best_run['file_name'],
                    'num_processes': best_run['num_processes'],
                    'Time': min_time,
                    'Speedup': speedup,
                    'Efficiency': efficiency,
                    'baseline_time': T1
                })
    
    return min_data

def plot_from_multiple_folders(base_dir, specific_folders=None):
    """Main function to process multiple data folders and create plots."""
    all_data = collect_all_data(base_dir, specific_folders)
    if not all_data:
        print("No data collected from folders.")
        return
    
    min_data = get_minimum_times(all_data)
    if not min_data:
        print("No minimum data calculated.")
        return
    
    df = pd.DataFrame(min_data)
    print(f"Created dataframe with {len(df)} rows")
    print(f"Data folders: {df['data_folder'].unique()}")
    print(f"Implementations: {df['implementation'].unique()}")
    print(f"Files: {df['file_name'].unique()}")
    
    _plot_dataframe(df, base_dir)


def _plot_dataframe(df: pd.DataFrame, log_dir: str = "logs"):
    os.makedirs(os.path.join(log_dir, "plots"), exist_ok=True)

    sns.set_style("whitegrid")

    # If we have multiple data folders, include them in the plots
    if 'data_folder' in df.columns and df['data_folder'].nunique() > 1:
        # Create a combined identifier for better visualization
        df['file_impl_folder'] = df['file_name'] + '_' + df['implementation'] + '_' + df['data_folder']
        hue_col = 'file_impl_folder'
        style_col = 'data_folder'
    else:
        df['file_impl'] = df['file_name'] + '_' + df['implementation']
        hue_col = 'file_impl'
        style_col = 'implementation'

    # Plot: Time
    plt.figure(figsize=(14, 8))
    sns.lineplot(
        data=df,
        x="num_processes",
        y="Time",
        hue=hue_col,
        style=style_col,
        markers=True,
        dashes=False,
    )
    plt.title("Performance Comparison (Minimum Times Across Runs)")
    plt.xlabel("Number of Processes")
    plt.ylabel("Time (s)")
    plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(os.path.join(log_dir, "plots", PLOT_FILE), dpi=300, bbox_inches='tight')
    plt.close()

    # Plot: Speedup
    plt.figure(figsize=(14, 8))
    sns.lineplot(
        data=df,
        x="num_processes",
        y="Speedup",
        hue=hue_col,
        style=style_col,
        markers=True,
        dashes=False,
    )
    plt.title("Speedup Comparison (Based on Minimum Times)")
    plt.xlabel("Number of Processes")
    plt.ylabel("Speedup")
    plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(os.path.join(log_dir, "plots", "speedup_plot.png"), dpi=300, bbox_inches='tight')
    plt.close()

    # Plot: Efficiency
    plt.figure(figsize=(14, 8))
    sns.lineplot(
        data=df,
        x="num_processes",
        y="Efficiency",
        hue=hue_col,
        style=style_col,
        markers=True,
        dashes=False,
    )
    plt.title("Efficiency Comparison (Based on Minimum Times)")
    plt.xlabel("Number of Processes")
    plt.ylabel("Efficiency")
    plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(os.path.join(log_dir, "plots", "efficiency_plot.png"), dpi=300, bbox_inches='tight')
    plt.close()

    # Save detailed CSV with all information
    df.to_csv(os.path.join(log_dir, "plots", "performance_metrics_minimum.csv"), index=False)
    
    # Create summary statistics
    summary_stats = df.groupby(['data_folder', 'implementation', 'file_name']).agg({
        'Time': ['min', 'mean'],
        'Speedup': ['max', 'mean'],
        'Efficiency': ['max', 'mean'],
        'num_processes': ['min', 'max']
    }).round(4)
    
    summary_stats.to_csv(os.path.join(log_dir, "plots", "summary_statistics.csv"))
    
    print(f"Summary statistics saved to: {os.path.join(log_dir, 'plots', 'summary_statistics.csv')}")


def plot_from_output_files(log_dir):
    """Original function for single folder processing (kept for backward compatibility)."""
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


def parse_folder_arguments(args):
    """Parse command line arguments to extract folder specifications."""
    folders = []
    base_dir = "logs"
    
    i = 0
    while i < len(args):
        if args[i] == "--dir":
            if i + 1 < len(args):
                base_dir = args[i + 1]
                i += 2
            else:
                print("Error: --dir requires a directory path")
                sys.exit(1)
        elif args[i] == "--folders":
            # Collect all folder names until next flag or end
            i += 1
            while i < len(args) and not args[i].startswith('--'):
                folders.append(args[i])
                i += 1
        elif args[i].startswith('--'):
            i += 1
        else:
            # Assume it's a folder name if it contains @ symbol
            if '@' in args[i]:
                folders.append(args[i])
            i += 1
    
    return base_dir, folders if folders else None


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print("Usage: python3 plot_results.py [options] [folder1] [folder2] ...")
        print("Options:")
        print("  --local                     Use original single CSV file method")
        print("  --dir <path>               Specify base directory (default: logs)")
        print("  --folders <f1> <f2> ...    Specify specific date@time folders")
        print("  --multi                    Process multiple date@time folders")
        print("")
        print("Examples:")
        print("  python3 plot_results.py 26_05_2025@01_14 27_05_2025@10_30")
        print("  python3 plot_results.py --dir /path/to/logs --folders 26_05_2025@01_14")
        print("  python3 plot_results.py --multi --dir logs")
        sys.exit(1)

    base_dir, specific_folders = parse_folder_arguments(sys.argv[1:])

    if "--local" in sys.argv:
        plot_results()
    elif specific_folders or "--multi" in sys.argv:
        print(f"Base directory: {base_dir}")
        if specific_folders:
            print(f"Processing specific folders: {specific_folders}")
        else:
            print("Processing all available date@time folders")
        plot_from_multiple_folders(base_dir, specific_folders)
    else:
        # Check if the directory has date@time structure
        data_folders = []
        try:
            for item in os.listdir(base_dir):
                if os.path.isdir(os.path.join(base_dir, item)) and '@' in item:
                    data_folders.append(item)
        except FileNotFoundError:
            pass
        
        if data_folders:
            print(f"Detected date@time folder structure, using multi-folder processing")
            plot_from_multiple_folders(base_dir)
        else:
            print(f"Using single folder processing")
            plot_from_output_files(base_dir)

    print(f"Processing complete. Check the plots folder for results.")