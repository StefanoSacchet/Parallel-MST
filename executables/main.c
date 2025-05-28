#include <stdio.h>
#include <stdlib.h>

#ifdef SERIAL
#include "serial_mst.h"
#elif defined(MPI)
#include "mpi_mst.h"
#elif defined(OMP)
#include "omp_mst.h"
#elif defined(HYBRID)
#include "hybrid_mst.h"
#endif

int main(int argc, char *argv[]) {
  if (argc != 2) {
    printf("Usage: ./parallel_ms <file_name>\n");
    return 1;
  }

#ifdef SERIAL
  run_serial_mst(argc, argv);
#elif defined(MPI)
  run_mpi_mst(argc, argv);
#elif defined(OMP)
  run_omp_mst(argc, argv);
#elif defined(HYBRID)
  run_hybrid_mst(argc, argv);
#endif

  return 0;
}
