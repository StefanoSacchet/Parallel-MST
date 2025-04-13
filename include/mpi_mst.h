#ifndef MPI_MST_H
#define MPI_MST_H

#include <mpi.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "common.h"

void custom_mpi_types(int *blocklengths, MPI_Aint *offsets);
void scatter_edge_list(Edge_t *edges, Edge_t *edges_part, const int n_edges, int *edges_per_core);
void run_mpi_mst(int argc, char *argv[]);
uint64_t mpi_mst(struct Graph *graph, struct Graph *mst);

#endif  // MPI_MST_H
