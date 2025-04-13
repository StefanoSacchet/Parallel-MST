#include "common.h"

#include <stdlib.h>

// Create a graph with V vertices and E edges
struct Graph *create_graph(int V, int E) {
  struct Graph *graph = (struct Graph *)malloc(sizeof(struct Graph));
  graph->V = V;
  graph->E = E;
  graph->edges = (struct Edge *)malloc(E * sizeof(struct Edge));
  return graph;
}

void free_graph(struct Graph *graph) {
  if (graph) {
    free(graph->edges);
    free(graph);
  }
}
