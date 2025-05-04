#ifndef COMMON_H
#define COMMON_H

#include <mpi.h>
#include <stdint.h>

// CORRESPONDING DEFINES AND TYPEDEFS NEED TO BE THE SAME

#define MPI_GRAPH_SIZE_T MPI_UINT64_T
#define MPI_EDGE_SIZE_T MPI_UINT64_T
#define MPI_EDGE_WEIGHT_T MPI_INT64_T

typedef uint64_t graph_size_t;
typedef uint64_t edge_t;
typedef int64_t edge_weight_t;

typedef uint64_t tot_mst_weight_t;

typedef struct Edge {
  edge_t src, dest;
  edge_weight_t weight;
} Edge_t;

typedef struct Graph {
  graph_size_t V, E;
  struct Edge *edges;
} Graph_t;

// Subset for union-find
typedef struct Subset {
  edge_t parent;
  graph_size_t rank;
} Subset_t;

// Initialize `graph` with `V` vertices and `E` edges
void init_graph(Graph_t *graph, graph_size_t V, graph_size_t E);
// Deallocate the graph
void free_graph(Graph_t *graph);

/** @brief Find parent of an element i (uses path compression)
 *
 * @param subset The array of subsets
 * @param i The node for which we want the parent
 */
edge_t find(Subset_t subsets[], edge_t i);

// Union of two sets by rank
void unionSets(Subset_t subsets[], edge_t x, edge_t y);

#endif  // COMMON_H
