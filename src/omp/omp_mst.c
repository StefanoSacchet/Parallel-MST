#include "omp_mst.h"

#include <omp.h>

#include "common.h"
#include "logger.h"
#include "tools/graph_parser.h"

void omp_mst(Graph_t *graph, Graph_t *mst) {
  graph_size_t n_edges = graph->E;
  graph_size_t n_vertices = graph->V;

  Edge_t *edges = graph->edges;

  // Init set
  Subset_t *subsets = (Subset_t *)malloc(n_vertices * sizeof(Subset_t));
  if (subsets == NULL) {
    fprintf(stderr, "Failed to allocate memory for subsets\n");
    exit(EXIT_FAILURE);
  }

  graph_size_t edges_mst = 0;

  // Cheapest outgoing edge for each component
  Edge_t *cheapest = (Edge_t *)malloc(n_vertices * sizeof(Edge_t));
  if (cheapest == NULL) {
    fprintf(stderr, "Failed to allocate memory for cheapest edges\n");
    exit(EXIT_FAILURE);
  }

  // Initialize subsets and cheapest array
  for (graph_size_t v = 0; v < n_vertices; v++) {
    subsets[v].parent = v;
    subsets[v].rank = 0;
    cheapest[v].weight = -1;
  }

  while (edges_mst < n_vertices - 1) {
    // Reset cheapest edges array
    for (graph_size_t j = 0; j < n_vertices; j++) {
      cheapest[j].weight = -1;
    }

    // Traverse through all edges and update cheapest of every component
    for (graph_size_t j = 0; j < n_edges; j++) {
      Edge_t current_edge = edges[j];
      graph_size_t set1 = find(subsets, current_edge.src);
      graph_size_t set2 = find(subsets, current_edge.dest);

      if (set1 != set2) {
        if (cheapest[set1].weight == -1 || cheapest[set1].weight > current_edge.weight) {
          cheapest[set1] = current_edge;
        }
        if (cheapest[set2].weight == -1 || cheapest[set2].weight > current_edge.weight) {
          cheapest[set2] = current_edge;
        }
      }
    }

    // Add new edges to MST
    for (graph_size_t j = 0; j < n_vertices; j++) {
      if (cheapest[j].weight != -1) {
        Edge_t edge = cheapest[j];

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
    printf("Running in sequential mode\n");

  parse_graph_file(graph, file_name);
  init_graph(mst, graph->V, graph->V - 1);

  double start_time = omp_get_wtime();
  omp_mst(graph, mst);
  double total_time = omp_get_wtime() - start_time;

  for (graph_size_t i = 0; i < mst->E; i++) {
    mst_weight += mst->edges[i].weight;
  }

  if (!HPC) {
    printf("Total time: %f\n", total_time);
    printf("Total weight of MST: %" PRIu64 "\n", mst_weight);
    log_result("seq", file_name, 1, total_time);
  }

  free_graph(mst);
  free_graph(graph);
  return mst_weight;
}
