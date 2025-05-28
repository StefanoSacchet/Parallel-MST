import glob
import os
import sys
from collections import defaultdict

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

COMBINED_FILE = "combined_plot.png"
SPEEDUP_FILE = "speedup_plot.png"
EFF_FILE = "efficiency_plot.png"

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


def extract_impl_and_processes_from_filename(filename):
    """Extract implementation type and number of processes from filename like 'omp_parallel_mst.o4'"""
    basename = os.path.basename(filename)
    if '_parallel_mst.o' in basename:
        parts = basename.split('_parallel_mst.o')
        impl_type = parts[0].upper()  # Convert to uppercase for consistency
        try:
            num_processes = int(parts[1])
            return impl_type, num_processes
        except ValueError:
            return None, None
    return None, None


def collect_all_data(base_dir, specific_folders=None):
    """Collect data from all folders and organize by implementation type."""
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
        
        # Look for all implementation files
        for run_folder in run_folders:
            run_folder_name = os.path.basename(run_folder)
            # Find all files matching *_parallel_mst.o* pattern
            pattern = "*_parallel_mst.o*"
            files = glob.glob(os.path.join(run_folder, pattern))
            print(f"  Found {len(files)} files in {run_folder_name}: {[os.path.basename(f) for f in files]}")
            
            for file_path in files:
                impl_type, file_processes = extract_impl_and_processes_from_filename(file_path)
                if impl_type is None:
                    print(f"    Could not parse implementation from {os.path.basename(file_path)}")
                    continue
                    
                data = read_file_data(file_path)
                if data:
                    # Verify consistency between filename and file content
                    if file_processes != data['num_processes']:
                        print(f"Warning: Process count mismatch in {file_path}: "
                              f"filename suggests {file_processes}, content says {data['num_processes']}")
                    
                    print(f"    Added data: {impl_type} {data['file_name']} {data['num_processes']}p {data['time']:.3f}s from {run_folder_name}")
                    
                    # Create a unique key for this configuration
                    config_key = (data['algorithm'], data['file_name'], data['num_processes'])
                    all_data[data_folder][impl_type][config_key].append(data)
                else:
                    print(f"    Could not read data from {os.path.basename(file_path)}")
    
    return all_data


def get_minimum_times_by_implementation(base_dir, all_data):
    """Get minimum times for each implementation separately."""

    serial_file = os.path.join(base_dir, "serial_parallel_mst.o1")
    global_baseline = read_base_time(serial_file)

    if global_baseline is None:
        print("Cannot calculate speedup/efficiency: base time not available.")
        return
    
    print(f"Using global baseline time: {global_baseline:.3f}s")
    
    # Now collect all results and find absolute minimums for each (impl, file, processes) combination
    impl_file_proc_minimums = {}
    
    for data_folder, impl_data in all_data.items():
        folder_name = os.path.basename(data_folder)
        
        for impl_type, configs in impl_data.items():
            if impl_type == 'SERIAL':
                continue  # Skip serial for plotting
            
            for config_key, runs in configs.items():
                if not runs:
                    continue
                
                algo, file_name, num_processes = config_key
                
                # Find minimum time across all runs for this configuration
                min_time = min(run['time'] for run in runs)
                best_run = min(runs, key=lambda x: x['time'])
                
                # Key for grouping results by implementation, file and process count
                group_key = (impl_type, file_name, num_processes)
                
                if group_key not in impl_file_proc_minimums or min_time < impl_file_proc_minimums[group_key]['Time']:
                    speedup = global_baseline / min_time
                    efficiency = speedup / num_processes
                    
                    impl_file_proc_minimums[group_key] = {
                        'data_folder': folder_name,
                        'implementation': impl_type,
                        'algorithm': best_run['algorithm'],
                        'file_name': file_name,
                        'num_processes': num_processes,
                        'Time': min_time,
                        'Speedup': speedup,
                        'Efficiency': efficiency,
                        'baseline_time': global_baseline
                    }
    
    return list(impl_file_proc_minimums.values())

def _plot_dataframe(df: pd.DataFrame, log_dir: str = "logs"):
    os.makedirs(os.path.join(log_dir, "plots"), exist_ok=True)

    sns.set_style("whitegrid")

    # Create a combined identifier for better visualization
    df['impl_file'] = df['implementation'] + ' - ' + df['file_name']

    # Plot: Time (separate lines for each implementation-file combination)
    plt.figure(figsize=(16, 10))
    sns.lineplot(
        data=df,
        x="num_processes",
        y="Time",
        hue="impl_file",
        style="implementation",
        markers=True,
        dashes=False,
        errorbar=None,
    )
    plt.title("Best Performance by Implementation and File (Minimum Times Across All Runs)")
    plt.xlabel("Number of Processes")
    plt.ylabel("Time (s)")
    plt.legend(title="Implementation - File", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(os.path.join(log_dir, "plots", COMBINED_FILE), dpi=300, bbox_inches='tight')
    plt.close()

    # Plot: Speedup (separate lines for each implementation-file combination)
    plt.figure(figsize=(16, 10))
    sns.lineplot(
        data=df,
        x="num_processes",
        y="Speedup",
        hue="impl_file",
        style="implementation",
        markers=True,
        dashes=False,
        errorbar=None,
    )
    plt.title("Best Speedup by Implementation and File (Based on Minimum Times)")
    plt.xlabel("Number of Processes")
    plt.ylabel("Speedup")
    plt.legend(title="Implementation - File", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(os.path.join(log_dir, "plots", SPEEDUP_FILE), dpi=300, bbox_inches='tight')
    plt.close()

    # Plot: Efficiency (separate lines for each implementation-file combination)
    plt.figure(figsize=(16, 10))
    sns.lineplot(
        data=df,
        x="num_processes",
        y="Efficiency",
        hue="impl_file",
        style="implementation",
        markers=True,
        dashes=False,
        errorbar=None,
    )
    plt.title("Best Efficiency by Implementation and File (Based on Minimum Times)")
    plt.xlabel("Number of Processes")
    plt.ylabel("Efficiency")
    plt.legend(title="Implementation - File", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(os.path.join(log_dir, "plots", EFF_FILE), dpi=300, bbox_inches='tight')
    plt.close()

    # Additional plots: Compare implementations directly for each file
    for file_name in df['file_name'].unique():
        file_data = df[df['file_name'] == file_name]
        
        if len(file_data) == 0:
            continue
            
        # Time comparison for this file
        plt.figure(figsize=(12, 8))
        sns.lineplot(
            data=file_data,
            x="num_processes",
            y="Time",
            hue="implementation",
            markers=True,
            dashes=False,
            errorbar=None,
        )
        plt.title(f"Performance Comparison for {file_name}")
        plt.xlabel("Number of Processes")
        plt.ylabel("Time (s)")
        plt.legend(title="Implementation")
        plt.tight_layout()
        safe_filename = file_name.replace('/', '_').replace('\\', '_')
        plt.savefig(os.path.join(log_dir, "plots", f"time_comparison_{safe_filename}.png"), 
                   dpi=300, bbox_inches='tight')
        plt.close()
        
        # Speedup comparison for this file
        plt.figure(figsize=(12, 8))
        sns.lineplot(
            data=file_data,
            x="num_processes",
            y="Speedup",
            hue="implementation",
            markers=True,
            dashes=False,
            errorbar=None,
        )
        plt.title(f"Speedup Comparison for {file_name}")
        plt.xlabel("Number of Processes")
        plt.ylabel("Speedup")
        plt.legend(title="Implementation")
        plt.tight_layout()
        plt.savefig(os.path.join(log_dir, "plots", f"speedup_comparison_{safe_filename}.png"), 
                   dpi=300, bbox_inches='tight')
        plt.close()

    # Save detailed CSV with minimum times per implementation per file per process count
    df_save = df.drop('impl_file', axis=1)  # Remove the combined column before saving
    df_save.to_csv(os.path.join(log_dir, "plots", "minimum_times_by_implementation.csv"), index=False)
    
    # Create summary showing best implementation for each file/process combination
    summary_data = []
    for file_name in df['file_name'].unique():
        for num_proc in sorted(df['num_processes'].unique()):
            file_proc_data = df[(df['file_name'] == file_name) & (df['num_processes'] == num_proc)]
            if len(file_proc_data) > 0:
                best_row = file_proc_data.loc[file_proc_data['Time'].idxmin()]
                summary_data.append({
                    'file_name': file_name,
                    'num_processes': num_proc,
                    'best_implementation': best_row['implementation'],
                    'best_time': best_row['Time'],
                    'speedup': best_row['Speedup'],
                    'efficiency': best_row['Efficiency'],
                    'data_folder': best_row['data_folder']
                })
    
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv(os.path.join(log_dir, "plots", "best_implementation_summary.csv"), index=False)
    
    print(f"Results by implementation saved to: {os.path.join(log_dir, 'plots', 'minimum_times_by_implementation.csv')}")
    print(f"Best implementation summary saved to: {os.path.join(log_dir, 'plots', 'best_implementation_summary.csv')}")
    
    # Print summary
    print(f"\nSummary by implementation:")
    for impl in sorted(df['implementation'].unique()):
        impl_data = df[df['implementation'] == impl]
        print(f"\n{impl}:")
        for file_name in sorted(impl_data['file_name'].unique()):
            file_data = impl_data[impl_data['file_name'] == file_name].sort_values('num_processes')
            print(f"  {file_name}:")
            for _, row in file_data.iterrows():
                print(f"    {row['num_processes']} processes: {row['Time']:.3f}s "
                      f"({row['Speedup']:.2f}x speedup, {row['Efficiency']:.2f} efficiency)")

def plot_from_multiple_folders(base_dir, specific_folders=None):
    """Main function to process multiple data folders and create plots."""
    all_data = collect_all_data(base_dir, specific_folders)
    if not all_data:
        print("No data collected from folders.")
        return
    
    min_data = get_minimum_times_by_implementation(base_dir, all_data)
    if not min_data:
        print("No minimum data calculated.")
        return
    
    df = pd.DataFrame(min_data)
    print(f"Created dataframe with {len(df)} rows")
    print(f"Data folders: {df['data_folder'].unique()}")
    print(f"Implementations: {df['implementation'].unique()}")
    print(f"Files: {df['file_name'].unique()}")
    
    _plot_dataframe(df, base_dir)

def plot_from_output_files(log_dir):
    """Single folder processing."""
    serial_file = os.path.join(log_dir, "serial_parallel_mst.o1")
    T1 = read_base_time(serial_file)

    if T1 is None:
        print("Cannot calculate speedup/efficiency: base time not available.")
        return

    patterns = [
        ("MPI", os.path.join(log_dir, "mpi_parallel_mst.o*")),
        ("OMP", os.path.join(log_dir, "omp_parallel_mst.o*")),
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

    if specific_folders or "--multi" in sys.argv:
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