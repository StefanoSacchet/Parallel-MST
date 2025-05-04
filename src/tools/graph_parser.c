#include "tools/graph_parser.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "common.h"

#define PATH_LEN 256
#define MAX_LINE_LENGTH 256

void parse_graph_file(Graph_t *graph, const char *filename) {
  char path[PATH_LEN];
  snprintf(path, sizeof(path), "%s/%s", DATASET_DIR, filename);
  FILE *file = fopen(path, "r");
  if (!file) {
    fprintf(stderr, "Error opening graph file: %s | PWD: %s\n", path, getcwd(NULL, 0));
    exit(EXIT_FAILURE);
  }

  char line[MAX_LINE_LENGTH];
  edge_t edge_index = 0;

  // Skip comments and read the first data line (should be: <V> <E>)
  while (fgets(line, sizeof(line), file)) {
    if (line[0] != '#') {
      graph_size_t V, E;
      if (sscanf(line, "%llu %llu", &V, &E) != 2) {
        fprintf(stderr, "Invalid graph header format (expected '<V> <E>')\n");
        fclose(file);
        exit(EXIT_FAILURE);
      }

      graph->V = V;
      graph->E = E;
      graph->edges = malloc(E * sizeof(Edge_t));
      if (!graph->edges) {
        perror("Memory allocation failed");
        fclose(file);
        exit(EXIT_FAILURE);
      }

      break;
    }
  }

  // Read the edges (skip comments, parse lines like: "0 1 32")
  while (fgets(line, sizeof(line), file)) {
    if (line[0] == '#')
      continue;

    edge_t src, dest;
    edge_weight_t weight;
    if (sscanf(line, "%llu %llu %lld", &src, &dest, &weight) == 3) {
      if (edge_index >= graph->E) {
        fprintf(stderr, "More edges than declared in header\n");
        fclose(file);
        exit(EXIT_FAILURE);
      }

      graph->edges[edge_index++] = (Edge_t){src, dest, weight};
    }
  }

  if (edge_index != graph->E) {
    fprintf(stderr, "Edge count mismatch: expected %llu, got %llu\n", graph->E, edge_index);
    fclose(file);
    exit(EXIT_FAILURE);
  }

  fclose(file);
}
