#ifndef COMMON_H
#define COMMON_H

#include <mpi.h>

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

struct Graph *create_graph(int V, int E);
void free_graph(struct Graph *graph);

#endif  // COMMON_H
