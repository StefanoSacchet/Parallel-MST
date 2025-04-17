#ifndef COMMON_H
#define COMMON_H

typedef struct Edge {
  int src, dest, weight;
} Edge_t;

typedef struct Graph {
  int V, E;
  struct Edge *edges;
} Graph_t;

// Subset for union-find
typedef struct Subset {
  int parent;
  int rank;
} Subset_t;

// Initialize `graph` with `V` vertices and `E` edges
void init_graph(Graph_t *graph, int V, int E);
// Deallocate the graph
void free_graph(struct Graph *graph);

/** @brief Find parent of an element i (uses path compression)
 *
 * @param subset The array of subsets
 * @param i The node for which we want the parent
 */
int find(struct Subset subsets[], int i);

// Union of two sets by rank
void unionSets(struct Subset subsets[], int x, int y);

#endif  // COMMON_H
