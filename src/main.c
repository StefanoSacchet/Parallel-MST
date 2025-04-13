#include "common.h"
#include "mpi_mst.h"
#include "serial_mst.h"

void serial_mst(void) {
  int V = 4;  // Number of vertices
  int E = 5;  // Number of edges
  Graph_t *graph = &(Graph_t){
      .V = 0,
      .E = 0,
      .edges = NULL,
  };
  init_graph(graph, V, E);

  graph->edges[0] = (struct Edge){0, 1, 10};
  graph->edges[1] = (struct Edge){0, 2, 6};
  graph->edges[2] = (struct Edge){0, 3, 5};
  graph->edges[3] = (struct Edge){1, 3, 15};
  graph->edges[4] = (struct Edge){2, 3, 4};

  int mst_weight = boruvkaMST(graph);
  printf("Total weight of MST: %d\n", mst_weight);

  free_graph(graph);
}

int main(int argc, char *argv[]) {
  // serial_mst();
  run_mpi_mst(argc, argv);

  return 0;
}
