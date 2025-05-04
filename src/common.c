#include "common.h"

#include <stdlib.h>

void init_graph(Graph_t *graph, graph_size_t V, graph_size_t E) {
  graph->V = V;
  graph->E = E;
  graph->edges = (struct Edge *)malloc(E * sizeof(struct Edge));
}

void free_graph(struct Graph *graph) {
  if (graph) {
    free(graph->edges);
  }
}

/** @brief Find parent of an element i (uses path compression)
 *
 * @param subset The array of subsets
 * @param i The node for which we want the parent
 */
edge_t find(struct Subset subsets[], edge_t i) {
  if (subsets[i].parent != i) {
    subsets[i].parent = find(subsets, subsets[i].parent);
  }
  return subsets[i].parent;
}

// Union of two sets by rank
void unionSets(struct Subset subsets[], edge_t x, edge_t y) {
  edge_t rootX = find(subsets, x);
  edge_t rootY = find(subsets, y);

  // Attach smaller rank tree under root of high rank tree
  if (rootX != rootY) {
    if (subsets[rootX].rank < subsets[rootY].rank) {
      subsets[rootX].parent = rootY;
    } else if (subsets[rootX].rank > subsets[rootY].rank) {
      subsets[rootY].parent = rootX;
    } else {
      subsets[rootY].parent = rootX;
      subsets[rootX].rank++;
    }
  }
}
