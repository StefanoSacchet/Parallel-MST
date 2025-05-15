#include <stdlib.h>

#include "mpi_mst.h"
#include "omp_mst.h"
#include "serial_mst.h"

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
#else
#error "Invalid RUN_TYPE: must be SERIAL or MPI"
#endif

  return 0;
}
