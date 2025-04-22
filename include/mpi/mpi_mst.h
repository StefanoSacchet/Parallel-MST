#ifndef MPI_MST_H
#define MPI_MST_H

#include <mpi.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "common.h"

/** @brief Dispatch edges to all processes
 *  @param edges The list containing all edges
 *  @param edges_part The list containing the edges for this process
 *  @param n_edges The number of edges in the graph
 *  @param edges_per_core The number of edges per core
 */
void scatter_edge_list(Edge_t *edges, Edge_t **edges_part_ptr, const int n_edges,
                       int *edges_per_core, int rank, int size);
// Run MPI MST
void run_mpi_mst(int argc, char *argv[]);
// Boruvka's algorithm with MPI
void mpi_mst(struct Graph *graph, struct Graph *mst);

#endif  // MPI_MST_H
