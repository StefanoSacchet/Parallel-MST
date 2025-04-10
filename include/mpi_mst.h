#ifndef MPI_MST_H
#define MPI_MST_H

#include <mpi.h>
#include <stdio.h>
#include <string.h>

#include "common.h"

void scatterEdgeList(Edge_t *edges, Edge_t *edges_part, const int n_edges, int *edges_per_core);
void run_mpi_mst(int argc, char *argv[]);
int mpi_mst(struct Graph *graph, struct Graph *mst);

#endif  // MPI_MST_H
