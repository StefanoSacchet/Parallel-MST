#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#include "graph_generator.h"

int main(int argc, char *argv[]) {
  if (argc != 3 && argc != 4) {
    fprintf(stderr, "Usage: %s <NUM_VERTICES> <NUM_EDGES> [OUTPUT_FILE]\n", argv[0]);
    fprintf(stderr, "If OUTPUT_FILE is not specified, output will be printed to stdout\n");
    return EXIT_FAILURE;
  }

  uint64_t num_vertices = strtoull(argv[1], NULL, 10);
  uint64_t num_edges = strtoull(argv[2], NULL, 10);

  if (num_edges < num_vertices - 1) {
    fprintf(stderr, "Error: Number of edges must be at least n-1 (where n is the "
                    "number of vertices)\n");
    return EXIT_FAILURE;
  }

  // Initialize random seed
  srand(time(NULL));

  // Generate graph
  Edge_t *edges = generate_random_graph(num_vertices, num_edges);

  // Write edges to file or stdout
  const char *output_file = (argc == 4) ? argv[3] : NULL;
  write_edges_to_file_or_stdout(output_file, edges, num_edges);

  // Cleanup
  free(edges);

  return EXIT_SUCCESS;
}
