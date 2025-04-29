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
  int edge_index = 0;
  int found_metadata = 0;

  // Look for metadata line
  while (fgets(line, sizeof(line), file)) {
    if (line[0] != '#')
      break;

    int V, E;
    if (sscanf(line, "# Vertices %d Edges %d", &V, &E) == 2) {
      graph->V = V;
      graph->E = E;
      graph->edges = malloc(E * sizeof(Edge_t));
      if (!graph->edges) {
        perror("Memory allocation failed");
        fclose(file);
        exit(EXIT_FAILURE);
      }
      found_metadata = 1;
    }
  }

  if (!found_metadata) {
    fprintf(stderr, "Graph metadata not found in header (expected '# Nodes: <V> Edges: "
                    "<E>')\n");
    fclose(file);
    exit(EXIT_FAILURE);
  }

  // Go back one line if necessary (last read line might be valid edge)
  do {
    int src, dest, weight;
    if (sscanf(line, "%d\t%d\t%d", &src, &dest, &weight) == 3) {
      if (edge_index >= graph->E) {
        fprintf(stderr, "More edges than declared in header\n");
        fclose(file);
        exit(EXIT_FAILURE);
      }

      graph->edges[edge_index++] = (Edge_t){src, dest, weight};
    }
  } while (fgets(line, sizeof(line), file));

  if (edge_index != graph->E) {
    fprintf(stderr, "Edge count mismatch: expected %d, got %d\n", graph->E, edge_index);
    fclose(file);
    exit(EXIT_FAILURE);
  }

  fclose(file);
}
