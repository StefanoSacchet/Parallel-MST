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

#endif  // COMMON_H
