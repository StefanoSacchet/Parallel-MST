# Parallel MST (Borůvka's Algorithm)

This project implements a parallel version of Borůvka’s algorithm for Minimum Spanning Tree (MST). It supports multiple modes (SERIAL, MPI, OMP, HYBRID) for high-performance computing (HPC).

## Repository Structure

-   [CMakeLists.txt](CMakeLists.txt): Main CMake configuration.
-   [Makefile](Makefile): Alternative build scripts, including targets for Debug, Release, and HPC configurations.
-   [executables](executables): Contains the distributed executables for different modes of the MST algorithm.
-   [include](include): Header files for the MST algorithm and supporting utilities.
-   [src](src): Source files for MST logic and supporting tools.
-   [dataset](dataset): Contains sample input graphs.

## Pre-requisites
-   **CMake**: Version 3.10 or higher.
-   **C++ Compiler**: Supports C++11 or higher.
-   **MPI**: For distributed execution (if using MPI mode).
-   **OpenMP**: For parallel execution (if using OpenMP mode).

## Building

You can build the project with either CMake or the Makefile:

```sh
# Using CMake:
mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release -DRUN_TYPE=ALL
make -j

# Using the Makefile:
make release (or debug)
```

For HPC-specific builds, use:

```sh
make release-hpc
```

`RUN_TYPE` can be set to `SERIAL`, `MPI`, `OMP`, `HYBRID`, `TESTS`, or`GEN_GRAPH` to specify what executable to compile.

## Running

Executables are places in [build/bin](build/bin). Depending on your RUN_TYPE, you’ll get binaries such as:
- `serial_mst`
- `mpi_mst`
- `omp_mst`
- `hybrid_mst`
- `graph_generator`
- `test_all`

To run on HPC there are several shell scripts in the `root` directory. Additionally, run `make help` to see available targets.

## Logging and Analytics
Logs from HPC runs are stored as .o and .e files. The Python script [`plot_results.py`](plot_results.py) parses them to compute average times, speedups, and efficiency.

Weak scalability uses different test cases, and expects different results, thereofore, the script [`plot_results_weak.py`](plot_results_weak.py) is provided for that purpose.

## Dataset

The [dataset](dataset) directory contains sample input graphs. The `graph_generator` executable can be used to create custom graphs.
