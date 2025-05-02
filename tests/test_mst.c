#include <assert.h>
#include <stdlib.h>

#include "common.h"
#include "mpi_mst.h"
#include "serial_mst.h"

void test_serial_mst(void) {
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

  int mst_weight = serial_mst(graph);

  free_graph(graph);

  assert(mst_weight == 19);
}

void test_mpi_vs_serial(void) {
  char *fake_argv[] = {"program_name", "small.txt"};
  uint64_t serial_tot_weight = run_serial_mst(2, fake_argv);
  uint64_t mpi_tot_weight = run_mpi_mst(2, fake_argv);
  assert(serial_tot_weight == mpi_tot_weight);
}

void test_mpi_vs_serial_2(void) {
  char *fake_argv[] = {"program_name", "small2.txt"};
  run_serial_mst(2, fake_argv);
  uint64_t serial_tot_weight = run_serial_mst(2, fake_argv);
  uint64_t mpi_tot_weight = run_mpi_mst(2, fake_argv);
  assert(serial_tot_weight == mpi_tot_weight);
}

int main(int argc, char **argv) {
  if (argc < 2) {
    fprintf(stderr, "Please specify test name (e.g., test_serial_mst)\n");
    return EXIT_FAILURE;
  }

  if (strcmp(argv[1], "test_serial_mst") == 0) {
    test_serial_mst();
  } else if (strcmp(argv[1], "test_mpi_vs_serial") == 0) {
    test_mpi_vs_serial();
  } else if (strcmp(argv[1], "test_mpi_vs_serial_2") == 0) {
    test_mpi_vs_serial_2();
  } else {
    fprintf(stderr, "Unknown test name: %s\n", argv[1]);
    return EXIT_FAILURE;
  }

  return EXIT_SUCCESS;
}
