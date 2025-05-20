#include "omp_mst.h"

#include <omp.h>
#include <stdlib.h>

#include "common.h"
#include "logger.h"
#include "tools/graph_parser.h"

void omp_mst(Graph_t *graph, Graph_t *mst) {
  graph_size_t n_edges = graph->E;
  graph_size_t n_vertices = graph->V;
  Edge_t *edges = graph->edges;

  Subset_t *subsets = (Subset_t *)malloc(n_vertices * sizeof(Subset_t));
  if (subsets == NULL) {
    fprintf(stderr, "Failed to allocate memory for subsets\n");
    exit(EXIT_FAILURE);
  }

  Edge_t *cheapest = (Edge_t *)malloc(n_vertices * sizeof(Edge_t));
  if (cheapest == NULL) {
    fprintf(stderr, "Failed to allocate memory for cheapest edges\n");
    free(subsets);
    exit(EXIT_FAILURE);
  }

  // Locks for each subset to protect concurrent writes to cheapest[]
  omp_lock_t *locks = malloc(n_vertices * sizeof(omp_lock_t));
#pragma omp simd
  for (graph_size_t i = 0; i < n_vertices; ++i) {
    omp_init_lock(&locks[i]);
  }

// Initialize subsets and cheapest
#pragma omp simd
  for (graph_size_t v = 0; v < n_vertices; ++v) {
    subsets[v].parent = v;
    subsets[v].rank = 0;
    cheapest[v].weight = -1;
  }

  graph_size_t edges_mst = 0;

  while (edges_mst < n_vertices - 1) {
// Reset cheapest array
#pragma omp simd
    for (graph_size_t i = 0; i < n_vertices; ++i) {
      cheapest[i].weight = -1;
    }

// Find cheapest edges for each component in parallel
#pragma omp parallel for schedule(auto)
    for (graph_size_t i = 0; i < n_edges; ++i) {
      Edge_t current_edge = edges[i];
      graph_size_t set1 = find(subsets, current_edge.src);
      graph_size_t set2 = find(subsets, current_edge.dest);

      if (set1 != set2) {
        omp_set_lock(&locks[set1]);
        if (cheapest[set1].weight == -1 || cheapest[set1].weight > current_edge.weight) {
          cheapest[set1] = current_edge;
        }
        omp_unset_lock(&locks[set1]);

        omp_set_lock(&locks[set2]);
        if (cheapest[set2].weight == -1 || cheapest[set2].weight > current_edge.weight) {
          cheapest[set2] = current_edge;
        }
        omp_unset_lock(&locks[set2]);
      }
    }

    // Add the selected cheapest edges to MST
    for (graph_size_t i = 0; i < n_vertices; ++i) {
      if (cheapest[i].weight != -1) {
        Edge_t edge = cheapest[i];
        graph_size_t from = find(subsets, edge.src);
        graph_size_t to = find(subsets, edge.dest);

        if (from != to) {
          mst->edges[edges_mst] = edge;
          edges_mst++;
          unionSets(subsets, from, to);
        }
      }
    }
  }

// Cleanup
#pragma omp simd
  for (graph_size_t i = 0; i < n_vertices; ++i) {
    omp_destroy_lock(&locks[i]);
  }
  free(locks);
  free(subsets);
  free(cheapest);
}

tot_mst_weight_t run_omp_mst(int argc, char *argv[]) {
  const char *file_name = argv[argc - 1];
  tot_mst_weight_t mst_weight = 0;

  Graph_t *graph = &(Graph_t){
      .V = 0,
      .E = 0,
      .edges = NULL,
  };
  Graph_t *mst = &(Graph_t){
      .V = 0,
      .E = 0,
      .edges = NULL,
  };

  if (DEBUG)
    printf("Running in OMP mode\n");

  parse_graph_file(graph, file_name);
  init_graph(mst, graph->V, graph->V - 1);

  double start_time = omp_get_wtime();
  omp_mst(graph, mst);
  double total_time = omp_get_wtime() - start_time;

  if (HPC) {
#pragma omp parallel
    if (omp_get_thread_num() == 0) {
      printf("omp %s %d %f\n", file_name, omp_get_num_threads(), total_time);
    }
  }

  for (graph_size_t i = 0; i < mst->E; i++) {
    mst_weight += mst->edges[i].weight;
  }

  if (!HPC) {
    printf("Total time: %f\n", total_time);
    printf("Total weight of MST: %" PRIu64 "\n", mst_weight);
    log_result("omp", file_name, 1, total_time);
  }

  free_graph(mst);
  free_graph(graph);
  return mst_weight;
}
