#ifndef MPI_MST_H
#define MPI_MST_H

#include <mpi.h>
#include <stdio.h>
#include <string.h>

#include "common.h"

// const int MAX_STRING = 100;

int parallel_boruvka_mst(struct Graph *graph);

#endif  // MPI_MST_H
