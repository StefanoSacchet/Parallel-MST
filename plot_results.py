import glob
import os
import sys
from collections import defaultdict

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

def read_base_time(serial_file):
    """Read the baseline serial time from serial file."""
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
            if os.path.isdir(item_path) and ('@' in item):
                data_folders.append(item_path)
    
    return sorted(data_folders)

def get_cpu_configurations(data_folder):
    """Get all CPU configurations (1_cpu, 2_cpu, 4_cpu, etc.) from a data folder."""
    cpu_configs = []
    for item in os.listdir(data_folder):
        item_path = os.path.join(data_folder, item)
        if os.path.isdir(item_path) and item.endswith('_cpu'):
            cpu_configs.append(item_path)
    return sorted(cpu_configs, key=lambda x: int(os.path.basename(x).split('_')[0]))

def get_strategies(cpu_config_path):
    """Get all strategies (pack, scatter) from a CPU configuration folder."""
    strategies = []
    for item in os.listdir(cpu_config_path):
        item_path = os.path.join(cpu_config_path, item)
        if os.path.isdir(item_path) and item in ['pack', 'scatter']:
            strategies.append(item_path)
    return sorted(strategies)

def get_run_folders(strategy_path):
    """Get all run folders (run_1, run_2, etc.) from a strategy folder."""
    run_folders = []
    for item in os.listdir(strategy_path):
        item_path = os.path.join(strategy_path, item)
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
            else:
                print(f"[WARNING] No line found. Possible empty file at '{file_path}'")
    except (FileNotFoundError, ValueError, IndexError) as e:
        print(f"Error reading file {file_path}: {e}")
    return None

def extract_impl_and_processes_from_filename(filename):
    """Extract implementation type and number of processes from filename."""
    basename = os.path.basename(filename)
    
    # Handle both pack and scatter strategies
    for strategy in ['pack', 'scatter']:
        pattern = f'_parallel_mst_{strategy}.o'
        if pattern in basename:
            parts = basename.split(pattern)
            impl_type = parts[0].upper()  # Convert to uppercase for consistency
            try:
                num_processes = int(parts[1])
                return impl_type, num_processes, strategy
            except ValueError:
                return None, None, None
    
    return None, None, None

def collect_all_data(base_dir, specific_folders=None):
    """Collect data from all folders and organize by CPU config, strategy, and implementation type."""
    # Structure: [data_folder][cpu_config][strategy][impl_type][config_key] = [run_data]
    all_data = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list)))))
    
    data_folders = find_data_folders(base_dir, specific_folders)
    if not data_folders:
        if specific_folders:
            print(f"None of the specified folders found: {specific_folders}")
        else:
            print(f"No date@time folders found in {base_dir}")
        return None
    
    print(f"Found {len(data_folders)} data folders: {[os.path.basename(f) for f in data_folders]}")
    
    for data_folder in data_folders:
        cpu_configs = get_cpu_configurations(data_folder)
        if not cpu_configs:
            print(f"No CPU configuration folders found in {data_folder}")
            continue
            
        print(f"Processing {len(cpu_configs)} CPU configurations in {os.path.basename(data_folder)}")
        
        for cpu_config_path in cpu_configs:
            cpu_config = os.path.basename(cpu_config_path)
            strategies = get_strategies(cpu_config_path)
            
            print(f"  CPU Config {cpu_config}: found {len(strategies)} strategies")
            n_cpus = int(cpu_config.split('_')[0])
            print(f"n cpus {n_cpus}")
            
            for strategy_path in strategies:
                strategy = os.path.basename(strategy_path)
                run_folders = get_run_folders(strategy_path)
                
                print(f"    Strategy {strategy}: found {len(run_folders)} run folders")
                
                for run_folder in run_folders:
                    run_folder_name = os.path.basename(run_folder)
                    
                    # Find all files matching parallel MST patterns
                    implementation_patterns = [
                        "*_parallel_mst_pack.o*",
                        "*_parallel_mst_scatter.o*"
                    ]
                    
                    all_files = []
                    for pattern in implementation_patterns:
                        files = glob.glob(os.path.join(run_folder, pattern))
                        # Filter out .o1 files
                        filtered_files = [f for f in files if not f.endswith('.o1')]
                        all_files.extend(filtered_files)
                    
                    if all_files:
                        print(f"      {run_folder_name}: found {len(all_files)} files (excluding .o1)")
                    
                    for file_path in all_files:
                        impl_type, file_processes, file_strategy = extract_impl_and_processes_from_filename(file_path)
                        
                        if impl_type is None:
                            print(f"        Could not parse implementation from {os.path.basename(file_path)}")
                            continue
                        
                        # Verify strategy consistency
                        if file_strategy != strategy:
                            print(f"        Strategy mismatch: folder={strategy}, file={file_strategy}")
                            continue
                            
                        data = read_file_data(file_path)
                        if data:
                            data['num_processes'] *= n_cpus
                            # Verify consistency between filename and file content
                            if file_processes != data['num_processes']:
                                print(f"        Process count mismatch in {os.path.basename(file_path)}: "
                                      f"filename={file_processes}, content={data['num_processes']}")
                            
                            # Create a unique key for this configuration
                            config_key = (data['algorithm'], data['file_name'], data['num_processes'])
                            
                            # Add CPU config and strategy info to data
                            data['cpu_config'] = cpu_config
                            data['strategy'] = strategy
                            data['data_folder'] = os.path.basename(data_folder)
                            
                            all_data[data_folder][cpu_config][strategy][impl_type][config_key].append(data)
                            
                            print(f"        Added: {impl_type} {cpu_config} {strategy} "
                                  f"{data['file_name']} {data['num_processes']}p {data['time']:.3f}s")
                        else:
                            print(f"        Could not read data from {os.path.basename(file_path)}")
    
    return all_data

def get_global_baseline(base_dir, graph_name):
    # Look for serial file in base directory
    serial_file = os.path.join(base_dir, f"serial_{graph_name}.o1")
    global_baseline = read_base_time(serial_file)
    
    if global_baseline:
        print(f"Found global baseline time: {global_baseline:.3f}s at '{serial_file}'")
    
    return global_baseline

def get_minimum_times_by_configuration(base_dir, all_data, graph_name):
    """Get minimum times for each configuration separately."""
    
    global_baseline = get_global_baseline(base_dir, graph_name)
                        
    if global_baseline is None:
        print("Cannot calculate speedup/efficiency: base time not available.")
        return []

    # Collect all results and find absolute minimums for each configuration
    config_minimums = {}
    for data_folder, cpu_data in all_data.items():
        folder_name = os.path.basename(data_folder)
        
        for cpu_config, strategy_data in cpu_data.items():
            for strategy, impl_data in strategy_data.items():
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
                        
                        # Key for grouping results
                        group_key = (impl_type, cpu_config, strategy, file_name, num_processes)
                        
                        if group_key not in config_minimums or min_time < config_minimums[group_key]['Time']:
                            speedup = global_baseline / min_time
                            efficiency = speedup / num_processes
                            
                            config_minimums[group_key] = {
                                'data_folder': folder_name,
                                'implementation': impl_type,
                                'cpu_config': cpu_config,
                                'strategy': strategy,
                                'algorithm': best_run['algorithm'],
                                'file_name': file_name,
                                'num_processes': num_processes,
                                'Time': min_time,
                                'Speedup': speedup,
                                'Efficiency': efficiency,
                                'baseline_time': global_baseline
                            }
    
    return list(config_minimums.values())


def create_combined_plots(df: pd.DataFrame, plots_folder):
    """Create the 6 combined comparison plots (all implementations together)."""
    # Set up plotting style
    sns.set_style("whitegrid")
    plt.rcParams['figure.dpi'] = 300
    plt.rcParams['font.size'] = 12
    
    # Define colors for implementations
    impl_colors = {
        'MPI': '#1f77b4',    # Blue
        'OMP': '#ff7f0e',    # Orange  
        'HYBRID': '#2ca02c'  # Green
    }
    
    # Define markers for CPU configurations
    cpu_markers = {
        '1_cpu': 'o',   # Circle
        '2_cpu': 's',   # Square
        '4_cpu': '^'    # Triangle
    }
    
    # Define mapping from CPU config to node labels
    cpu_to_node_label = {
        '1_cpu': '1 node',
        '2_cpu': '2 nodes', 
        '4_cpu': '3 nodes'
    }
    
    # Filter data to only include the implementations and CPU configs we want
    target_impls = ['MPI', 'OMP', 'HYBRID']
    target_cpus = ['1_cpu', '2_cpu', '4_cpu']
    
    filtered_df = df[
        (df['implementation'].isin(target_impls)) & 
        (df['cpu_config'].isin(target_cpus))
    ]
    
    print(f"Filtered data: {len(filtered_df)} rows from {len(df)} total rows")
    print(f"Implementations: {sorted(filtered_df['implementation'].unique())}")
    print(f"CPU configs: {sorted(filtered_df['cpu_config'].unique())}")
    print(f"Strategies: {sorted(filtered_df['strategy'].unique())}")
    
    # Create the 6 combined plots
    strategies = ['pack', 'scatter']
    metrics = [('Time', 'Time (s)'), ('Speedup', 'Speedup'), ('Efficiency', 'Efficiency')]
    
    for strategy in strategies:
        strategy_data = filtered_df[filtered_df['strategy'] == strategy]
        
        if len(strategy_data) == 0:
            print(f"No data found for strategy: {strategy}")
            continue
            
        print(f"\nCreating combined plots for {strategy.upper()} strategy...")
        
        for metric, ylabel in metrics:
            plt.figure(figsize=(14, 8))
            
            # Plot each implementation separately to control colors and markers
            for impl in target_impls:
                impl_data = strategy_data[strategy_data['implementation'] == impl]
                
                if len(impl_data) == 0:
                    continue
                
                # Plot each CPU configuration with different markers
                for cpu_config in target_cpus:
                    cpu_data = impl_data[impl_data['cpu_config'] == cpu_config]
                    
                    if len(cpu_data) == 0:
                        continue
                    
                    # Sort by number of processes for clean lines
                    cpu_data = cpu_data.sort_values('num_processes')
                    
                    plt.plot(
                        cpu_data['num_processes'], 
                        cpu_data[metric],
                        color=impl_colors[impl],
                        marker=cpu_markers[cpu_config],
                        markersize=8,
                        linewidth=2,
                        label=f"{impl} - {cpu_config}",
                        linestyle='-' if impl == 'MPI' else '--' if impl == 'OMP' else '-.'
                    )            
            plt.title(f'{metric} Comparison - {strategy.upper()} Strategy\n(MPI, OMP, HYBRID - 1, 2, 4 CPU)', 
                     fontsize=14, fontweight='bold')
            plt.xlabel('Number of Processes', fontsize=12)
            plt.ylabel(ylabel, fontsize=12)
            
            plt.grid(True, alpha=0.3)
            plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=10)
            
            # Set x-axis to show all process counts
            process_counts = sorted(strategy_data['num_processes'].unique())
            plt.xticks(process_counts)
            
            plt.tight_layout()
            
            # Save the plot
            filename = f"{metric.lower()}_{strategy}_comparison.png"
            filepath = os.path.join(plots_folder, filename)
            plt.savefig(filepath, bbox_inches='tight', dpi=300)
            plt.close()
            
            print(f"  Saved: {filename}")


def create_separated_plots(df: pd.DataFrame, plots_folder):
    """Create separate plots for each implementation (MPI, OMP, HYBRID)."""
    # Set up plotting style
    sns.set_style("whitegrid")
    plt.rcParams['figure.dpi'] = 300
    plt.rcParams['font.size'] = 12
    
    # Define colors for CPU configurations (different from implementation colors)
    cpu_colors = {
        '1_cpu': '#e74c3c',   # Red
        '2_cpu': '#3498db',   # Blue
        '4_cpu': '#2ecc71'    # Green
    }
    
    # Define markers for strategies
    strategy_markers = {
        'pack': 'o',      # Circle
        'scatter': 's'    # Square
    }
    
    # Filter data
    target_impls = ['MPI', 'OMP', 'HYBRID']
    target_cpus = ['1_cpu', '2_cpu', '4_cpu']
    
    filtered_df = df[
        (df['implementation'].isin(target_impls)) & 
        (df['cpu_config'].isin(target_cpus))
    ]
    
    print(f"\nCreating separated plots for each implementation...")
    
    strategies = ['pack', 'scatter']
    metrics = [('Time', 'Time (s)'), ('Speedup', 'Speedup'), ('Efficiency', 'Efficiency')]
    
    # Create plots for each implementation separately
    for impl in target_impls:
        impl_data = filtered_df[filtered_df['implementation'] == impl]
        
        if len(impl_data) == 0:
            print(f"No data found for implementation: {impl}")
            continue
        
        print(f"\nCreating plots for {impl} implementation...")
        
        for metric, ylabel in metrics:
            plt.figure(figsize=(14, 8))
            
            # Plot each strategy and CPU configuration
            for strategy in strategies:
                strategy_data = impl_data[impl_data['strategy'] == strategy]
                
                if len(strategy_data) == 0:
                    continue
                
                for cpu_config in target_cpus:
                    cpu_data = strategy_data[strategy_data['cpu_config'] == cpu_config]
                    
                    if len(cpu_data) == 0:
                        continue
                    
                    # Sort by number of processes for clean lines
                    cpu_data = cpu_data.sort_values('num_processes')
                    
                    plt.plot(
                        cpu_data['num_processes'], 
                        cpu_data[metric],
                        color=cpu_colors[cpu_config],
                        marker=strategy_markers[strategy],
                        markersize=8,
                        linewidth=2,
                        label=f"{cpu_config} - {strategy}",
                        linestyle='-' if strategy == 'pack' else '--'
                    )   
                             
            plt.title(f'{metric} Analysis - {impl} Implementation\n(Pack vs Scatter - 1, 2, 4 CPU)', 
                     fontsize=14, fontweight='bold')
            plt.xlabel('Number of Processes', fontsize=12)
            plt.ylabel(ylabel, fontsize=12)
            
            plt.grid(True, alpha=0.3)
            plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=10)
            
            # Set x-axis to show all process counts
            process_counts = sorted(impl_data['num_processes'].unique())
            plt.xticks(process_counts)
            
            plt.tight_layout()
            
            # Save the plot
            filename = f"{metric.lower()}_{impl.lower()}_separated.png"
            filepath = os.path.join(plots_folder, filename)
            plt.savefig(filepath, bbox_inches='tight', dpi=300)
            plt.close()
            
            print(f"  Saved: {filename}")


def create_focused_plots(df: pd.DataFrame, graph_name, log_dir: str = "logs"):
    """Create both combined and separated plots."""
    plots_folder = os.path.join(log_dir, "plots_" + graph_name)
    os.makedirs(plots_folder, exist_ok=True)
    
    # Create combined plots (original functionality)
    create_combined_plots(df, plots_folder)
    
    # Create separated plots (new functionality)
    create_separated_plots(df, plots_folder)
    
    # Create summary tables for each strategy
    strategies = ['pack', 'scatter']
    target_impls = ['MPI', 'OMP', 'HYBRID']
    target_cpus = ['1_cpu', '2_cpu', '4_cpu']
    
    filtered_df = df[
        (df['implementation'].isin(target_impls)) & 
        (df['cpu_config'].isin(target_cpus))
    ]
    
    for strategy in strategies:
        strategy_data = filtered_df[filtered_df['strategy'] == strategy]
        
        if len(strategy_data) == 0:
            continue
        
        # Create summary table
        summary_table = strategy_data.pivot_table(
            index=['implementation', 'cpu_config'],
            columns='num_processes',
            values=['Time', 'Speedup', 'Efficiency'],
            aggfunc='first'
        ).round(3)
        
        # Save summary table
        summary_filename = f"summary_{strategy}_strategy.csv"
        summary_filepath = os.path.join(log_dir, "plots", summary_filename)
        summary_table.to_csv(summary_filepath)
        print(f"Saved summary table: {summary_filename}")
    
    # Print analysis summary
    print(f"\n" + "="*60)
    print(f"ENHANCED ANALYSIS SUMMARY")
    print(f"="*60)
    
    for strategy in strategies:
        strategy_data = filtered_df[filtered_df['strategy'] == strategy]
        
        if len(strategy_data) == 0:
            continue
            
        print(f"\n{strategy.upper()} Strategy Results:")
        print(f"-" * 30)
        
        # Best performance for each implementation
        for impl in target_impls:
            impl_data = strategy_data[strategy_data['implementation'] == impl]
            
            if len(impl_data) == 0:
                print(f"  {impl}: No data available")
                continue
            
            best_time = impl_data.loc[impl_data['Time'].idxmin()]
            best_speedup = impl_data.loc[impl_data['Speedup'].idxmax()]
            
            print(f"  {impl}:")
            print(f"    Best Time: {best_time['Time']:.3f}s ({best_time['cpu_config']}, {best_time['num_processes']} proc)")
            print(f"    Best Speedup: {best_speedup['Speedup']:.2f}x ({best_speedup['cpu_config']}, {best_speedup['num_processes']} proc)")
            print(f"    Best Efficiency: {best_speedup['Efficiency']:.3f}")
    
    print(f"\nGenerated plots:")
    print(f"  Combined comparison plots (6 total):")
    print(f"    - time_pack_comparison.png")
    print(f"    - speedup_pack_comparison.png") 
    print(f"    - efficiency_pack_comparison.png")
    print(f"    - time_scatter_comparison.png")
    print(f"    - speedup_scatter_comparison.png")
    print(f"    - efficiency_scatter_comparison.png")
    print(f"  Separated implementation plots (9 total):")
    print(f"    - time_mpi_separated.png")
    print(f"    - speedup_mpi_separated.png")
    print(f"    - efficiency_mpi_separated.png")
    print(f"    - time_omp_separated.png")
    print(f"    - speedup_omp_separated.png")
    print(f"    - efficiency_omp_separated.png")
    print(f"    - time_hybrid_separated.png")
    print(f"    - speedup_hybrid_separated.png")
    print(f"    - efficiency_hybrid_separated.png")
    print(f"\nAll plots saved to: {os.path.join(log_dir, 'plots')}")


def plot_focused_analysis(base_dir, specific_folders=None):
    """Main function to create the focused plots."""
    all_data = collect_all_data(base_dir, specific_folders)
    if not all_data:
        print("No data collected from folders.")
        return

    graph_name = next(iter(k[1] for d1 in all_data.values()
                            for d2 in d1.values()
                            for d3 in d2.values()
                            for d4 in d3.values()
                            for k in d4.keys())).split('/')[1].split('.')[0]

    min_data = get_minimum_times_by_configuration(base_dir, all_data, graph_name)
    if not min_data:
        print("No minimum data calculated.")
        return
    
    df = pd.DataFrame(min_data)
    print(f"Created dataframe with {len(df)} rows")
    print(f"Data folders: {df['data_folder'].unique()}")
    print(f"CPU configurations: {df['cpu_config'].unique()}")
    print(f"Strategies: {df['strategy'].unique()}")
    print(f"Implementations: {df['implementation'].unique()}")
    print(f"Files: {df['file_name'].unique()}")
    
    create_focused_plots(df, graph_name, base_dir)


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
        print("MST Performance Plotter")
        print("===============================")
        print("Creates 15 total plots:")
        print("  COMBINED PLOTS (6 total):")
        print("    - Time, Speedup, Efficiency for Pack strategy")
        print("    - Time, Speedup, Efficiency for Scatter strategy")
        print("    - Each plot shows MPI, OMP, HYBRID implementations together")
        print("    - Each plot shows 1, 2, 4 CPU configurations")
        print("  SEPARATED PLOTS (9 total):")
        print("    - Time, Speedup, Efficiency for each implementation (MPI, OMP, HYBRID)")
        print("    - Each plot shows Pack vs Scatter strategies")
        print("    - Each plot shows 1, 2, 4 CPU configurations")
        print("")
        print("Usage: python3 enhanced_plotter.py [options] [folder1] [folder2] ...")
        print("Options:")
        print("  --dir <path>               Specify base directory (default: logs)")
        print("  --folders <f1> <f2> ...    Specify specific date@time folders")
        print("")
        print("Examples:")
        print("  python3 enhanced_plotter.py 26_05_2025@01_14 27_05_2025@10_30")
        print("  python3 enhanced_plotter.py --dir /path/to/logs --folders 26_05_2025@01_14")
        print("  python3 enhanced_plotter.py --dir logs")
        sys.exit(1)

    base_dir, specific_folders = parse_folder_arguments(sys.argv[1:])

    print(f"Enhanced MST Performance Analysis")
    print(f"Base directory: {base_dir}")
    if specific_folders:
        print(f"Processing specific folders: {specific_folders}")
    else:
        print("Processing all available date@time folders")
    
    plot_focused_analysis(base_dir, specific_folders)
    print(f"Enhanced analysis complete!")