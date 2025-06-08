#!/usr/bin/env python3
"""
Weak Scalability Analysis Tool

This script analyzes weak scalability data from MST (Minimum Spanning Tree) algorithm
implementations across different parallelization modes (MPI, OpenMP, Hybrid).
"""

import argparse
import os
import re
import glob
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
from pathlib import Path
from math import trunc

def parse_directory_name(dir_name):
    """
    Parse directory name to extract vertices and edges.
    Expected format: weak_scalabilityVkEk where V = vertices (in thousands), E = edges (in thousands)
    Example: weak_scalability1k5k means 1000 vertices, 5000 edges
    """
    pattern = r'weak_scalability(\d+)k(\d+)k'
    match = re.match(pattern, dir_name)
    if match:
        vertices = int(match.group(1)) * 1000  # Convert k to actual number
        edges = int(match.group(2)) * 1000     # Convert k to actual number
        return vertices, edges
    return None, None

def parse_data_file(file_path):
    """
    Parse data file and extract timing information.
    Expected format: mode file_path n_proc time
    """
    data = []
    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):  # Skip empty lines and comments
                    parts = line.split()
                    if len(parts) >= 4:
                        mode = os.path.splitext(os.path.basename(file_path))[0].split('_')[0]
                        file_path_used = parts[1]
                        n_proc = int(parts[2])  
                        time = float(parts[3])
                        data.append({
                            'mode': mode,
                            'file_path': file_path_used,
                            'n_proc': n_proc,
                            'time': time
                        })
    except (IOError, ValueError) as e:
        print(f"Warning: Could not parse file {file_path}: {e}")
    
    return data

def parse_serial_filename(filename):
    """
    Parse serial baseline filename to extract vertices and edges.
    Expected format: serial_VkEk.o1 where V = vertices (in thousands), E = edges (in thousands)
    Example: serial_25k800k.o1 means 25000 vertices, 800000 edges
    """
    pattern = r'serial_(\d+)k(\d+)k\.o\d+'
    match = re.match(pattern, filename)
    if match:
        vertices = int(match.group(1)) * 1000
        edges = int(match.group(2)) * 1000
        return vertices, edges
    return None, None

def collect_serial_baselines(base_dir):
    """
    Collect serial baseline times from the base directory.
    """
    baselines = {}
    base_path = Path(base_dir)
    
    # Find all serial baseline files
    serial_files = glob.glob(str(base_path / "serial_*k*k.o*"))
    
    for file_path in serial_files:
        filename = os.path.basename(file_path)
        vertices, edges = parse_serial_filename(filename)
        if vertices is None or edges is None:
            print(f"Warning: Could not parse serial filename {filename}")
            continue
        
        file_data = parse_data_file(file_path)
        if file_data:
            # Take the first (and should be only) entry
            baseline_time = file_data[0]['time']
            problem_size = f"{vertices//1000}k{edges//1000}k"
            baselines[problem_size] = baseline_time
            if len(file_data) > 1:
                print(f"Warning: Multiple entries found in serial file {filename}, using first one")
    
    return baselines

def collect_data(base_dir):
    """
    Collect all timing data from the directory structure.
    """
    all_data = []
    base_path = Path(base_dir)
    
    # Find all weak_scalability directories
    for dir_path in base_path.iterdir():
        if dir_path.is_dir() and dir_path.name.startswith('weak_scalability'):
            vertices, edges = parse_directory_name(dir_path.name)
            if vertices is None or edges is None:
                print(f"Warning: Could not parse directory name {dir_path.name}")
                continue
            
            # Find all data files in this directory
            data_files = glob.glob(str(dir_path / "*_parallel_mst_pack.o*"))
            
            for file_path in data_files:
                file_data = parse_data_file(file_path)
                for entry in file_data:
                    entry['vertices'] = vertices
                    entry['edges'] = edges
                    entry['problem_size'] = f"{vertices//1000}k{edges//1000}k"
                    all_data.append(entry)
    
    return pd.DataFrame(all_data)

def calculate_efficiency(df, baselines):
    """
    Calculate parallel efficiency for weak scalability using serial baselines.
    Efficiency = Speedup / n_proc
    """
    df_with_efficiency = df.copy()
    df_with_efficiency['efficiency'] = np.nan
    
    for idx, row in df_with_efficiency.iterrows():
        problem_size = row['problem_size']
        n_proc = row['n_proc']
        if problem_size in baselines:
            serial_time = baselines[problem_size]
            parallel_time = row['time']
            speedup = serial_time / parallel_time
            efficiency = speedup / n_proc
            df_with_efficiency.loc[idx, 'efficiency'] = trunc(efficiency * 10) / 10.0
        else:
            print(f"Warning: No serial baseline found for problem size {problem_size}")
    
    return df_with_efficiency

def create_scalability_plots(df, baselines, output_dir):
    """
    Create weak scalability efficiency plots with edge labels on data points.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Calculate efficiency using serial baselines
    df_with_eff = calculate_efficiency(df, baselines)
    
    # Create one plot for each mode (mpi, omp, hybrid)
    for mode in ['mpi', 'omp', 'hybrid']:
        mode_data = df_with_eff[df_with_eff['mode'] == mode]
        
        if mode_data.empty:
            print(f"Warning: No data available for mode {mode}")
            continue
        
        plt.figure(figsize=(10, 6))
        
        # Plot efficiency vs process number
        mode_data_sorted = mode_data.sort_values('n_proc')
        
        if not mode_data_sorted.empty and not mode_data_sorted['efficiency'].isna().all():
            # Plot the line
            plt.plot(mode_data_sorted['n_proc'], mode_data_sorted['efficiency'], 
                    marker='o', color='#1f77b4', linewidth=2, markersize=8,
                    linestyle='-', markerfacecolor='yellow', markeredgecolor='#1f77b4', 
                    markeredgewidth=2)
            
            # Add edge count labels on each data point
            for _, row in mode_data_sorted.iterrows():
                if not pd.isna(row['efficiency']):
                    # Format edge count as "X M" where X is edges in millions
                    edge_label = f"{row['edges'] // 1000000} M"

                    plt.annotate(edge_label, 
                               (row['n_proc'], row['efficiency']),
                               textcoords="offset points", 
                               xytext=(0, 10), 
                               ha='center', 
                               fontsize=10,
                               fontweight='bold')
        
        # Add ideal efficiency line
        plt.axhline(y=1.0, color='black', linestyle='--', alpha=0.7, linewidth=1)
        
        plt.xlabel('Number of parallel processes', fontsize=12)
        plt.ylabel('Efficiency', fontsize=12)
        plt.title('Weak Scalability Graph', fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
        
        # Set x-axis ticks to show actual process numbers
        if not mode_data_sorted.empty:
            proc_numbers = sorted(mode_data_sorted['n_proc'].unique())
            plt.xticks(proc_numbers, [str(p) for p in proc_numbers])
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'weak_scalability_{mode}.png'), 
                   dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Created weak scalability graph for {mode.upper()}")
    
    # Create a combined plot with all three modes
    plt.figure(figsize=(12, 8))
    
    colors = {'mpi': '#1f77b4', 'omp': '#ff7f0e', 'hybrid': '#2ca02c'}
    
    for mode in ['mpi', 'omp', 'hybrid']:
        mode_data = df_with_eff[df_with_eff['mode'] == mode].sort_values('n_proc')
        
        if not mode_data.empty and not mode_data['efficiency'].isna().all():
            plt.plot(mode_data['n_proc'], mode_data['efficiency'], 
                    marker='o', color=colors[mode], linewidth=2, markersize=8,
                    label=mode.upper(), linestyle='-', markerfacecolor='white', 
                    markeredgecolor=colors[mode], markeredgewidth=2)
            
            # Add edge count labels on each data point
            for _, row in mode_data.iterrows():
                if not pd.isna(row['efficiency']):
                    edge_label = f"{row['edges'] // 1000000} M"
                    plt.annotate(edge_label, 
                               (row['n_proc'], row['efficiency']),
                               textcoords="offset points", 
                               xytext=(0, 10), 
                               ha='center', 
                               fontsize=9,
                               fontweight='bold',
                               color=colors[mode])
    
    plt.axhline(y=1.0, color='black', linestyle='--', alpha=0.7, linewidth=1, label='Ideal')
    
    plt.xlabel('Number of parallel processes', fontsize=12)
    plt.ylabel('Efficiency', fontsize=12)
    plt.title('Weak Scalability Comparison - All Modes', fontsize=14, fontweight='bold')
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
    
    # Set x-axis ticks
    if not df_with_eff.empty:
        proc_numbers = sorted(df_with_eff['n_proc'].unique())
        plt.xticks(proc_numbers, [str(p) for p in proc_numbers])
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'weak_scalability_combined.png'), 
               dpi=300, bbox_inches='tight')
    plt.close()
    
    print("Created combined weak scalability comparison graph")

def generate_summary_report(df, baselines, output_dir):
    """
    Generate a summary report of the scalability analysis.
    """
    report_path = os.path.join(output_dir, 'scalability_report.txt')
    
    with open(report_path, 'w') as f:
        f.write("Weak Scalability Analysis Report\n")
        f.write("=" * 40 + "\n\n")
        
        f.write(f"Total data points: {len(df)}\n")
        f.write(f"Modes analyzed: {', '.join(df['mode'].unique())}\n")
        f.write(f"Problem sizes: {', '.join(sorted(df['problem_size'].unique()))}\n")
        f.write(f"Process counts range: {df['n_proc'].min()} - {df['n_proc'].max()}\n")
        f.write(f"Serial baselines found: {len(baselines)}\n\n")
        
        # Serial baseline times
        f.write("Serial Baseline Times:\n")
        f.write("-" * 25 + "\n")
        for problem_size, time in sorted(baselines.items()):
            f.write(f"  {problem_size}: {time:.4f}s\n")
        
        # Summary statistics by mode
        f.write("\nSummary by Mode:\n")
        f.write("-" * 20 + "\n")
        for mode in df['mode'].unique():
            mode_data = df[df['mode'] == mode]
            f.write(f"\n{mode.upper()}:\n")
            f.write(f"  Data points: {len(mode_data)}\n")
            f.write(f"  Avg execution time: {mode_data['time'].mean():.4f}s\n")
            f.write(f"  Min execution time: {mode_data['time'].min():.4f}s\n")
            f.write(f"  Max execution time: {mode_data['time'].max():.4f}s\n")
        
        # Efficiency analysis
        df_with_eff = calculate_efficiency(df, baselines)
        f.write("\n\nEfficiency Analysis:\n")
        f.write("-" * 20 + "\n")
        for mode in df_with_eff['mode'].unique():
            mode_data = df_with_eff[df_with_eff['mode'] == mode]
            valid_eff = mode_data['efficiency'].dropna()
            if not valid_eff.empty:
                f.write(f"\n{mode.upper()}:\n")
                f.write(f"  Avg efficiency: {valid_eff.mean():.4f}\n")
                f.write(f"  Best efficiency: {valid_eff.max():.4f}\n")
                f.write(f"  Worst efficiency: {valid_eff.min():.4f}\n")
        
        # Best performing configurations
        f.write("\n\nBest Performing Configurations:\n")
        f.write("-" * 30 + "\n")
        for problem_size in df['problem_size'].unique():
            subset = df[df['problem_size'] == problem_size]
            best_config = subset.loc[subset['time'].idxmin()]
            f.write(f"\n{problem_size}:\n")
            f.write(f"  Best: {best_config['mode'].upper()} with {best_config['n_proc']} processes\n")
            f.write(f"  Time: {best_config['time']:.4f}s\n")
            if problem_size in baselines:
                efficiency = baselines[problem_size] / best_config['time']
                f.write(f"  Efficiency: {efficiency:.4f}\n")

def main():
    parser = argparse.ArgumentParser(
        description='Analyze weak scalability data for MST algorithm implementations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  python weak_scalability_analyzer.py /path/to/data
        """
    )
    
    parser.add_argument('basedir', 
                       help='Base directory containing weak scalability data')
    
    args = parser.parse_args()
    output = os.path.join(args.basedir, "scalability_res")

    if not os.path.exists(args.basedir):
        print(f"Error: Base directory '{args.basedir}' does not exist.")
        return 1
    
    # Collect all data
    print("Collecting data...")
    df = collect_data(args.basedir)
    
    if df.empty:
        print("Error: No parallel data found. Please check the directory structure and file formats.")
        return 1
    
    # Collect serial baselines
    print("Collecting serial baselines...")
    baselines = collect_serial_baselines(args.basedir)
    
    if not baselines:
        print("Warning: No serial baseline files found. Efficiency calculations will not be available.")
    
    # Create plots
    print("Creating scalability plots...")
    create_scalability_plots(df, baselines, output)
    
    # Generate summary report
    print("Generating summary report...")
    generate_summary_report(df, baselines, output)
    
    print(f"\nAnalysis complete! Results saved to: {output}")
    print("Generated files:")
    print(f"  - MPI weak scalability: weak_scalability_mpi.png")
    print(f"  - OpenMP weak scalability: weak_scalability_omp.png") 
    print(f"  - Hybrid weak scalability: weak_scalability_hybrid.png")
    print(f"  - Combined comparison: weak_scalability_combined.png")
    print(f"  - Summary report: scalability_report.txt")
    
    return 0

if __name__ == '__main__':
    exit(main())