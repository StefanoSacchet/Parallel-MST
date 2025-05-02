#include "graph_generator.h"

#include <omp.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define MAX_WEIGHT 1000
#define PATH_SIZE 256

void ensure_connectivity(Edge_t *edges, uint64_t num_vertices) {
  for (uint64_t i = 0; i < num_vertices - 1; i++) {
    edges[i].src = i;
    edges[i].dest = i + 1;
    edges[i].weight = (rand() % MAX_WEIGHT) + 1;
  }
}

Edge_t *generate_random_graph(uint64_t num_vertices, uint64_t num_edges) {
  // Allocate memory for edges
  Edge_t *edges = (Edge_t *)malloc(num_edges * sizeof(Edge_t));
  if (!edges) {
    fprintf(stderr, "Memory allocation failed\n");
    exit(1);
  }

  // Ensure basic connectivity first
  ensure_connectivity(edges, num_vertices);

// Generate remaining random edges
#pragma omp parallel
  {
    unsigned int seed = omp_get_thread_num() + time(NULL);

#pragma omp for
    for (uint64_t i = num_vertices - 1; i < num_edges; i++) {
      do {
        edges[i].src = rand_r(&seed) % num_vertices;
        edges[i].dest = rand_r(&seed) % num_vertices;
      } while (edges[i].src == edges[i].dest);

      edges[i].weight = (rand_r(&seed) % MAX_WEIGHT) + 1;

      if (edges[i].src > edges[i].dest) {
        uint64_t temp = edges[i].src;
        edges[i].src = edges[i].dest;
        edges[i].dest = temp;
      }
    }
  }

  return edges;
}

void write_edges_to_file_or_stdout(const char *filename, Edge_t *edges, uint64_t num_edges) {
  FILE *f = NULL;

  // If filename is NULL or empty, use stdout
  if (filename == NULL || filename[0] == '\0') {
    f = stdout;
  } else {
    // Create the directory if it doesn't exist
    char command[PATH_SIZE];
    snprintf(command, sizeof(command), "mkdir -p %s/generated", DATASET_DIR);
    int ret = system(command);
    if (ret == -1) {
      fprintf(stderr, "Failed to create directory: %s\n", DATASET_DIR);
      return;
    }

    char path[PATH_SIZE];
    snprintf(path, sizeof(path), "%s/generated/%s", DATASET_DIR, filename);
    f = fopen(path, "w");
    if (!f) {
      fprintf(stderr, "Cannot open file for writing: %s\n", path);
      return;
    }
  }

  uint64_t max_vertex = 0;
  for (uint64_t i = 0; i < num_edges; i++) {
    if (edges[i].src > max_vertex) {
      max_vertex = edges[i].src;
    }
    if (edges[i].dest > max_vertex) {
      max_vertex = edges[i].dest;
    }
  }
  fprintf(f, "%llu %llu\n", max_vertex + 1, num_edges);

  for (uint64_t i = 0; i < num_edges; i++) {
    fprintf(f, "%d %d %d\n", edges[i].src, edges[i].dest, edges[i].weight);
  }

  if (f != stdout) {
    fclose(f);
  }
}
