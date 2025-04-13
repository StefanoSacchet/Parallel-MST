#include "mpi_types.h"

#include "common.h"

void create_mpi_edge_type(MPI_Datatype *mpi_edge_t) {
  int blocklengths[3] = {1, 1, 1};
  MPI_Aint offsets[3];
  MPI_Datatype oldtypes[3] = {MPI_INT, MPI_INT, MPI_INT};

  offsets[0] = offsetof(Edge_t, src);
  offsets[1] = offsetof(Edge_t, dest);
  offsets[2] = offsetof(Edge_t, weight);

  MPI_Type_create_struct(3, blocklengths, offsets, oldtypes, mpi_edge_t);
  MPI_Type_commit(mpi_edge_t);
}

void free_mpi_edge_type(MPI_Datatype *mpi_edge_t) {
  MPI_Type_free(mpi_edge_t);
}
