#ifndef MPI_MST_H
#define MPI_MST_H

#include <mpi.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "common.h"

/** @brief Dispatch edges to all processes
 * @param `edges`             Pointer to the global list of edges (only used on
 * rank 0).
 * @param `edges_part_ptr`    Pointer to the local edge list pointer to be
 * allocated and filled.
 * @param `n_edges`           Total number of edges in the graph (same on all
 * ranks).
 * @param `edges_per_core`    Pointer to the number of edges this process will
 * receive.
 * @param `rank`              Rank of the current MPI process.
 * @param `size`              Total number of MPI processes. */
void scatter_edge_list(Edge_t *edges, Edge_t **edges_part_ptr, const graph_size_t n_edges,
                       graph_size_t *edges_per_core, int rank, int size);
// Run MPI MST
tot_mst_weight_t run_mpi_mst(int argc, char *argv[]);
/**
 * @brief Compute the Minimum Spanning Tree (MST) using Borůvka's algorithm with
 * MPI.
 *
 * @param `graph` Input graph
 * @param `mst` Output MST graph
 */
void mpi_mst(Graph_t *graph, Graph_t *mst);

#endif  // MPI_MST_H
