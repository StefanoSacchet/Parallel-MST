#include <stdlib.h>

#include "mpi_mst.h"

#if !defined(SERIAL) && !defined(MPI)
#define SERIAL
#endif

int main(int argc, char *argv[]) {
  if (argc != 2) {
    printf("Usage: ./parallel_ms <file_name>\n");
    return 1;
  }

#ifdef SERIAL
  printf("Running in SERIAL mode\n");
  run_serial_mst(argc, argv);
#elif defined(MPI)
  run_mpi_mst(argc, argv);
#else
#error "Invalid RUN_TYPE: must be SERIAL or MPI"
#endif

  return 0;
}
