#include <assert.h>
#include <stdio.h>
#include <stdlib.h>

#include "common.h"
#include "serial_mst.h"

void test_serial_mst(void) {
  int V = 4;  // Number of vertices
  int E = 5;  // Number of edges
  struct Graph *graph = create_graph(V, E);
  graph->edges[0] = (struct Edge){0, 1, 10};
  graph->edges[1] = (struct Edge){0, 2, 6};
  graph->edges[2] = (struct Edge){0, 3, 5};
  graph->edges[3] = (struct Edge){1, 3, 15};
  graph->edges[4] = (struct Edge){2, 3, 4};

  int mst_weight = boruvkaMST(graph);

  free(graph->edges);
  free(graph);

  assert(mst_weight == 19);
}

int main(void) {
  test_serial_mst();
  return 0;
}
