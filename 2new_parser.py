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
    except (FileNotFoundError, ValueError, IndexError) as e:
        print(f"Error reading file {file_path}: {e}")
    return None


def extract_impl_and_processes_from_filename(filename):
    """Extract implementation type and number of processes from filename like 'mpi_parallel_mst_pack.o4'"""
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
            
            for strategy_path in strategies:
                strategy = os.path.basename(strategy_path)
                run_folders = get_run_folders(strategy_path)
                
                print(f"    Strategy {strategy}: found {len(run_folders)} run folders")
                
                for run_folder in run_folders:
                    run_folder_name = os.path.basename(run_folder)
                    
                    # Find all files matching *_parallel_mst_{pack,scatter}.o* pattern
                    for strategy_type in ['pack', 'scatter']:
                        pattern = f"*_parallel_mst_{strategy_type}.o*"
                        files = glob.glob(os.path.join(run_folder, pattern))
                        
                        if files:
                            print(f"      {run_folder_name} ({strategy_type}): found {len(files)} files")
                        
                        for file_path in files:
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


def get_minimum_times_by_configuration(base_dir, all_data):
    """Get minimum times for each configuration separately."""
    
    # Look for serial file in base directory
    serial_file = os.path.join(base_dir, "serial_parallel_mst.o1")
    global_baseline = read_base_time(serial_file)

    if global_baseline is None:
        print("Cannot calculate speedup/efficiency: base time not available.")
        return []
    
    print(f"Using global baseline time: {global_baseline:.3f}s")
    
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


def _plot_dataframe(df: pd.DataFrame, log_dir: str = "logs"):
    """Create comprehensive plots for the MST performance analysis."""
    os.makedirs(os.path.join(log_dir, "plots"), exist_ok=True)
    
    sns.set_style("whitegrid")
    plt.rcParams['figure.dpi'] = 300
    
    # Create combined identifiers for better visualization
    df['config_id'] = df['cpu_config'] + ' - ' + df['strategy']
    df['impl_config'] = df['implementation'] + ' (' + df['config_id'] + ')'
    df['full_config'] = df['implementation'] + ' - ' + df['cpu_config'] + ' - ' + df['strategy']
    
    # 1. Overall Performance Comparison
    plt.figure(figsize=(16, 10))
    sns.lineplot(
        data=df,
        x="num_processes",
        y="Time",
        hue="full_config",
        style="implementation",
        markers=True,
        dashes=False,
        errorbar=None,
    )
    plt.title("Performance Comparison: All Configurations")
    plt.xlabel("Number of Processes")
    plt.ylabel("Time (s)")
    plt.yscale('log')
    plt.legend(title="Configuration", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(os.path.join(log_dir, "plots", "overall_performance.png"), bbox_inches='tight')
    plt.close()
    
    # 2. Speedup Comparison
    plt.figure(figsize=(16, 10))
    sns.lineplot(
        data=df,
        x="num_processes",
        y="Speedup",
        hue="full_config",
        style="implementation",
        markers=True,
        dashes=False,
        errorbar=None,
    )
    plt.title("Speedup Comparison: All Configurations")
    plt.xlabel("Number of Processes")
    plt.ylabel("Speedup")
    # Add ideal speedup line
    max_processes = df['num_processes'].max()
    plt.plot([1, max_processes], [1, max_processes], 'k--', alpha=0.5, label='Ideal Speedup')
    plt.legend(title="Configuration", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(os.path.join(log_dir, "plots", SPEEDUP_FILE), bbox_inches='tight')
    plt.close()
    
    # 3. Efficiency Comparison
    plt.figure(figsize=(16, 10))
    sns.lineplot(
        data=df,
        x="num_processes",
        y="Efficiency",
        hue="full_config",
        style="implementation",
        markers=True,
        dashes=False,
        errorbar=None,
    )
    plt.title("Efficiency Comparison: All Configurations")
    plt.xlabel("Number of Processes")
    plt.ylabel("Efficiency")
    plt.axhline(y=1.0, color='k', linestyle='--', alpha=0.5, label='Perfect Efficiency')
    plt.legend(title="Configuration", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(os.path.join(log_dir, "plots", EFF_FILE), bbox_inches='tight')
    plt.close()
    
    # 4. Strategy Comparison (Pack vs Scatter)
    plt.figure(figsize=(14, 10))
    for impl in df['implementation'].unique():
        impl_data = df[df['implementation'] == impl]
        
        plt.subplot(2, 2, 1 if impl == 'MPI' else 2)
        sns.lineplot(
            data=impl_data,
            x="num_processes",
            y="Time",
            hue="strategy",
            style="cpu_config",
            markers=True,
            errorbar=None,
        )
        plt.title(f"{impl} - Time Comparison")
        plt.ylabel("Time (s)")
        plt.yscale('log')
        
        plt.subplot(2, 2, 3 if impl == 'MPI' else 4)
        sns.lineplot(
            data=impl_data,
            x="num_processes",
            y="Speedup",
            hue="strategy",
            style="cpu_config",
            markers=True,
            errorbar=None,
        )
        plt.title(f"{impl} - Speedup Comparison")
        plt.xlabel("Number of Processes")
        plt.ylabel("Speedup")
    
    plt.tight_layout()
    plt.savefig(os.path.join(log_dir, "plots", "strategy_comparison.png"), bbox_inches='tight')
    plt.close()
    
    # 5. CPU Configuration Analysis
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # Time by CPU config
    sns.lineplot(
        data=df,
        x="num_processes",
        y="Time",
        hue="cpu_config",
        style="implementation",
        markers=True,
        ax=axes[0,0],
        errorbar=None,
    )
    axes[0,0].set_title("Performance by CPU Configuration")
    axes[0,0].set_yscale('log')
    
    # Speedup by CPU config
    sns.lineplot(
        data=df,
        x="num_processes",
        y="Speedup",
        hue="cpu_config",
        style="implementation",
        markers=True,
        ax=axes[0,1],
        errorbar=None,
    )
    axes[0,1].set_title("Speedup by CPU Configuration")
    
    # Efficiency by CPU config
    sns.lineplot(
        data=df,
        x="num_processes",
        y="Efficiency",
        hue="cpu_config",
        style="implementation",
        markers=True,
        ax=axes[1,0],
        errorbar=None,
    )
    axes[1,0].set_title("Efficiency by CPU Configuration")
    
    # Strategy effectiveness per CPU config
    strategy_effectiveness = df.groupby(['cpu_config', 'strategy', 'num_processes'])['Speedup'].mean().reset_index()
    sns.lineplot(
        data=strategy_effectiveness,
        x="num_processes",
        y="Speedup",
        hue="strategy",
        style="cpu_config",
        markers=True,
        ax=axes[1,1],
        errorbar=None,
    )
    axes[1,1].set_title("Strategy Effectiveness by CPU Config")
    
    plt.tight_layout()
    plt.savefig(os.path.join(log_dir, "plots", "cpu_config_analysis.png"), bbox_inches='tight')
    plt.close()
    
    # 6. Graph-specific analysis (detailed analysis per input graph)
    print(f"\nGenerating graph-specific analysis for {len(df['file_name'].unique())} graphs...")
    
    for file_name in df['file_name'].unique():
        file_data = df[df['file_name'] == file_name]
        
        if len(file_data) == 0:
            continue
            
        safe_filename = file_name.replace('/', '_').replace('\\', '_').replace('.', '_')
        
        # Comprehensive 4-panel analysis for each graph
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # Time comparison
        sns.lineplot(
            data=file_data,
            x="num_processes",
            y="Time",
            hue="full_config",
            markers=True,
            errorbar=None,
            ax=axes[0,0]
        )
        axes[0,0].set_title(f"Performance - {file_name}")
        axes[0,0].set_ylabel("Time (s)")
        axes[0,0].set_yscale('log')
        axes[0,0].legend(bbox_to_anchor=(1.05, 1), loc="upper left")
        
        # Speedup comparison
        sns.lineplot(
            data=file_data,
            x="num_processes",
            y="Speedup",
            hue="full_config",
            markers=True,
            errorbar=None,
            ax=axes[0,1]
        )
        axes[0,1].set_title(f"Speedup - {file_name}")
        axes[0,1].set_ylabel("Speedup")
        # Add ideal speedup line
        max_proc = file_data['num_processes'].max()
        axes[0,1].plot([1, max_proc], [1, max_proc], 'k--', alpha=0.5, label='Ideal')
        axes[0,1].legend(bbox_to_anchor=(1.05, 1), loc="upper left")
        
        # Strategy comparison for this graph
        sns.lineplot(
            data=file_data,
            x="num_processes",
            y="Time",
            hue="strategy",
            style="implementation",
            markers=True,
            errorbar=None,
            ax=axes[1,0]
        )
        axes[1,0].set_title(f"Strategy Comparison - {file_name}")
        axes[1,0].set_ylabel("Time (s)")
        axes[1,0].set_yscale('log')
        
        # CPU configuration effectiveness for this graph
        sns.lineplot(
            data=file_data,
            x="num_processes",
            y="Speedup",
            hue="cpu_config",
            style="strategy",
            markers=True,
            errorbar=None,
            ax=axes[1,1]
        )
        axes[1,1].set_title(f"CPU Config Effectiveness - {file_name}")
        axes[1,1].set_ylabel("Speedup")
        
        plt.tight_layout()
        plt.savefig(os.path.join(log_dir, "plots", f"graph_analysis_{safe_filename}.png"), 
                   bbox_inches='tight', dpi=300)
        plt.close()
        
        # Create a detailed table for this graph
        graph_summary = file_data.pivot_table(
            index=['implementation', 'cpu_config', 'strategy'],
            columns='num_processes',
            values=['Time', 'Speedup', 'Efficiency'],
            aggfunc='first'
        ).round(3)
        
        graph_summary.to_csv(os.path.join(log_dir, "plots", f"graph_summary_{safe_filename}.csv"))
    
    # 7. Cross-graph comparison plots
    print("Generating cross-graph comparison plots...")
    
    # Compare how different graphs scale with each configuration
    plt.figure(figsize=(16, 12))
    
    # Create subplots for each implementation-strategy combination
    configs = df[['implementation', 'strategy']].drop_duplicates()
    n_configs = len(configs)
    cols = 2
    rows = (n_configs + 1) // 2
    
    for i, (_, config_row) in enumerate(configs.iterrows()):
        impl = config_row['implementation']
        strategy = config_row['strategy']
        
        config_data = df[(df['implementation'] == impl) & (df['strategy'] == strategy)]
        
        plt.subplot(rows, cols, i + 1)
        sns.lineplot(
            data=config_data,
            x="num_processes",
            y="Speedup",
            hue="file_name",
            style="cpu_config",
            markers=True,
            errorbar=None,
        )
        plt.title(f"{impl} - {strategy}")
        plt.ylabel("Speedup")
        if i >= (rows - 1) * cols:  # Only show x-label on bottom row
            plt.xlabel("Number of Processes")
        else:
            plt.xlabel("")
    
    plt.suptitle("Graph Scaling Comparison Across Configurations", fontsize=16)
    plt.tight_layout()
    plt.savefig(os.path.join(log_dir, "plots", "cross_graph_scaling.png"), 
               bbox_inches='tight', dpi=300)
    plt.close()
    
    # Graph characteristics analysis
    plt.figure(figsize=(14, 10))
    
    # Average performance per graph (normalized by best time for each graph)
    graph_performance = []
    for file_name in df['file_name'].unique():
        file_data = df[df['file_name'] == file_name]
        best_time = file_data['Time'].min()
        
        for _, row in file_data.iterrows():
            graph_performance.append({
                'file_name': file_name,
                'config': f"{row['implementation']}-{row['strategy']}",
                'num_processes': row['num_processes'],
                'normalized_time': row['Time'] / best_time,
                'speedup': row['Speedup']
            })
    
    graph_perf_df = pd.DataFrame(graph_performance)
    
    plt.subplot(2, 1, 1)
    sns.boxplot(data=graph_perf_df, x='file_name', y='normalized_time')
    plt.title("Performance Variation Across Graphs (Normalized by Best Time)")
    plt.ylabel("Normalized Time")
    plt.xticks(rotation=45)
    
    plt.subplot(2, 1, 2)
    sns.boxplot(data=graph_perf_df, x='file_name', y='speedup')
    plt.title("Speedup Distribution Across Graphs")
    plt.ylabel("Speedup")
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig(os.path.join(log_dir, "plots", "graph_characteristics.png"), 
               bbox_inches='tight', dpi=300)
    plt.close()
    
    # Save detailed results
    df_save = df.drop(['config_id', 'impl_config', 'full_config'], axis=1)
    df_save.to_csv(os.path.join(log_dir, "plots", "detailed_results.csv"), index=False)
    
    # Create performance summary (enhanced with graph-specific insights)
    summary_data = []
    graph_summary_data = []
    
    # Overall best configurations
    for cpu_config in df['cpu_config'].unique():
        for strategy in df['strategy'].unique():
            for num_proc in sorted(df['num_processes'].unique()):
                config_data = df[
                    (df['cpu_config'] == cpu_config) & 
                    (df['strategy'] == strategy) & 
                    (df['num_processes'] == num_proc)
                ]
                if len(config_data) > 0:
                    best_row = config_data.loc[config_data['Time'].idxmin()]
                    summary_data.append({
                        'cpu_config': cpu_config,
                        'strategy': strategy,
                        'num_processes': num_proc,
                        'best_implementation': best_row['implementation'],
                        'best_time': best_row['Time'],
                        'speedup': best_row['Speedup'],
                        'efficiency': best_row['Efficiency'],
                        'file_name': best_row['file_name'],
                        'data_folder': best_row['data_folder']
                    })
    
    # Graph-specific best configurations
    for file_name in df['file_name'].unique():
        file_data = df[df['file_name'] == file_name]
        
        for cpu_config in file_data['cpu_config'].unique():
            for strategy in file_data['strategy'].unique():
                for num_proc in sorted(file_data['num_processes'].unique()):
                    config_data = file_data[
                        (file_data['cpu_config'] == cpu_config) & 
                        (file_data['strategy'] == strategy) & 
                        (file_data['num_processes'] == num_proc)
                    ]
                    if len(config_data) > 0:
                        best_row = config_data.loc[config_data['Time'].idxmin()]
                        graph_summary_data.append({
                            'graph_name': file_name,
                            'cpu_config': cpu_config,
                            'strategy': strategy,
                            'num_processes': num_proc,
                            'best_implementation': best_row['implementation'],
                            'best_time': best_row['Time'],
                            'speedup': best_row['Speedup'],
                            'efficiency': best_row['Efficiency'],
                            'data_folder': best_row['data_folder']
                        })
        
        # Best overall configuration for this graph
        best_for_graph = file_data.loc[file_data['Time'].idxmin()]
        graph_summary_data.append({
            'graph_name': file_name,
            'cpu_config': 'BEST_OVERALL',
            'strategy': best_for_graph['strategy'],
            'num_processes': best_for_graph['num_processes'],
            'best_implementation': best_for_graph['implementation'],
            'best_time': best_for_graph['Time'],
            'speedup': best_for_graph['Speedup'],
            'efficiency': best_for_graph['Efficiency'],
            'data_folder': best_for_graph['data_folder']
        })
    
    summary_df = pd.DataFrame(summary_data)
    graph_summary_df = pd.DataFrame(graph_summary_data)
    
    summary_df.to_csv(os.path.join(log_dir, "plots", "performance_summary.csv"), index=False)
    graph_summary_df.to_csv(os.path.join(log_dir, "plots", "graph_specific_summary.csv"), index=False)
    
    print(f"Detailed results saved to: {os.path.join(log_dir, 'plots', 'detailed_results.csv')}")
    print(f"Performance summary saved to: {os.path.join(log_dir, 'plots', 'performance_summary.csv')}")
    print(f"Graph-specific summary saved to: {os.path.join(log_dir, 'plots', 'graph_specific_summary.csv')}")
    
    # Print analysis summary with graph-specific insights
    print(f"\nPerformance Analysis Summary:")
    print(f"Configurations analyzed: {len(df)}")
    print(f"Graphs tested: {sorted(df['file_name'].unique())}")
    print(f"CPU Configurations: {sorted(df['cpu_config'].unique())}")
    print(f"Strategies: {sorted(df['strategy'].unique())}")
    print(f"Implementations: {sorted(df['implementation'].unique())}")
    print(f"Process counts: {sorted(df['num_processes'].unique())}")
    
    # Best overall performance
    best_overall = df.loc[df['Time'].idxmin()]
    print(f"\nBest overall performance:")
    print(f"  Graph: {best_overall['file_name']}")
    print(f"  {best_overall['implementation']} - {best_overall['cpu_config']} - {best_overall['strategy']}")
    print(f"  {best_overall['num_processes']} processes: {best_overall['Time']:.3f}s")
    print(f"  Speedup: {best_overall['Speedup']:.2f}x, Efficiency: {best_overall['Efficiency']:.2f}")
    
    # Best configuration for each graph
    print(f"\nBest configuration per graph:")
    for file_name in sorted(df['file_name'].unique()):
        file_data = df[df['file_name'] == file_name]
        best_for_file = file_data.loc[file_data['Time'].idxmin()]
        print(f"  {file_name}:")
        print(f"    {best_for_file['implementation']} - {best_for_file['cpu_config']} - {best_for_file['strategy']}")
        print(f"    {best_for_file['num_processes']} processes: {best_for_file['Time']:.3f}s ({best_for_file['Speedup']:.2f}x speedup)")
    
    # Strategy effectiveness analysis
    print(f"\nStrategy effectiveness summary:")
    strategy_analysis = df.groupby(['strategy', 'file_name'])['Speedup'].mean().unstack()
    print("Average speedup by strategy and graph:")
    for strategy in strategy_analysis.index:
        print(f"  {strategy.upper()}:")
        for graph in strategy_analysis.columns:
            if not pd.isna(strategy_analysis.loc[strategy, graph]):
                print(f"    {graph}: {strategy_analysis.loc[strategy, graph]:.2f}x")
    
    print(f"\nGenerated plots:")
    print(f"  - Overall performance comparison")
    print(f"  - Speedup and efficiency analysis") 
    print(f"  - Strategy comparison (pack vs scatter)")
    print(f"  - CPU configuration analysis")
    print(f"  - Individual graph analysis (one per input graph)")
    print(f"  - Cross-graph scaling comparison")
    print(f"  - Graph characteristics analysis")


def plot_from_multiple_folders(base_dir, specific_folders=None):
    """Main function to process multiple data folders and create plots."""
    all_data = collect_all_data(base_dir, specific_folders)
    if not all_data:
        print("No data collected from folders.")
        return
    
    min_data = get_minimum_times_by_configuration(base_dir, all_data)
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
    
    _plot_dataframe(df, base_dir)


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
        print("")
        print("Expected folder structure:")
        print("  logs/data@time/")
        print("  ├── 1_cpu/pack/{1,...,n}_run/{mpi,omp}_parallel_mst_pack.o{2,4,8,...,64}")
        print("  ├── 2_cpu/pack/{1,...,n}_run/{mpi,omp}_parallel_mst_pack.o{4,8,16,...,64}")
        print("  ├── 2_cpu/scatter/{1,...,n}_run/{mpi,omp}_parallel_mst_scatter.o{4,8,16,...,64}")
        print("  └── 4_cpu/{pack,scatter}/{1,...,n}_run/...")
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
            print(f"No date@time folders found in {base_dir}")
            sys.exit(1)

    print(f"Processing complete. Check the plots folder for results.")