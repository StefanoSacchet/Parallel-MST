#ifndef MPI_TYPES_H
#define MPI_TYPES_H

#include "mpi.h"

void create_mpi_edge_type(MPI_Datatype *mpi_edge_t);
void free_mpi_edge_type(MPI_Datatype *mpi_edge_t);

#endif  // MPI_TYPES_H
