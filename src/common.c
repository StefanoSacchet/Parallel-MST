#include "common.h"

#include <stdlib.h>

void init_graph(Graph_t *graph, int V, int E) {
  graph->V = V;
  graph->E = E;
  graph->edges = (struct Edge *)malloc(E * sizeof(struct Edge));
}

void free_graph(struct Graph *graph) {
  if (graph) {
    free(graph->edges);
  }
}
