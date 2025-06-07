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

  graph_size_t total_bytes = sizeof(Subset_t) * n_vertices +  // for subsets
                             sizeof(Edge_t) * n_vertices +    // for cheapest
                             sizeof(Edge_t) * n_vertices;     // for candidates

  void *base_ptr = malloc(total_bytes);
  if (base_ptr == NULL) {
    fprintf(stderr, "Failed to allocate memory block\n");
    exit(EXIT_FAILURE);
  }

  Subset_t *subsets = (Subset_t *)base_ptr;
  Edge_t *cheapest = (Edge_t *)((char *)base_ptr + sizeof(Subset_t) * n_vertices);
  Edge_t *candidates = (Edge_t *)((char *)cheapest + sizeof(Edge_t) * n_vertices);

  graph_size_t edges_mst = 0;
  graph_size_t n_candidates = 0;

  // Initialize subsets in parallel
#pragma omp simd
  for (graph_size_t v = 0; v < n_vertices; ++v) {
    subsets[v].parent = v;
    subsets[v].rank = 0;
    cheapest[v].weight = -1;
  }

  // Temporary buffer for edge candidates
  Edge_t *local_cheapest;
  int num_threads;

#pragma omp parallel
  {
#pragma omp single
    {
      num_threads = omp_get_num_threads();
      local_cheapest = (Edge_t *)malloc(n_vertices * num_threads * sizeof(Edge_t));
      if (local_cheapest == NULL) {
        fprintf(stderr, "Failed to allocate memory for thread-local edges\n");
        free(base_ptr);
        exit(EXIT_FAILURE);
      }
    }
  }

  while (edges_mst < n_vertices - 1) {
#pragma omp parallel for simd schedule(static)
    for (graph_size_t i = 0; i < n_vertices; ++i) {
      cheapest[i].weight = -1;
    }

// Each thread finds local cheapest edges
#pragma omp parallel
    {
      int tid = omp_get_thread_num();
      Edge_t *my_cheapest = &local_cheapest[tid * n_vertices];

      // Initialize thread-local cheapest array
      for (graph_size_t i = 0; i < n_vertices; ++i) {
        my_cheapest[i].weight = -1;
      }

#pragma omp for schedule(auto)
      for (graph_size_t i = 0; i < n_edges; ++i) {
        Edge_t current_edge = edges[i];
        graph_size_t set1 = find(subsets, current_edge.src);
        graph_size_t set2 = find(subsets, current_edge.dest);

        if (set1 != set2) {
          if (my_cheapest[set1].weight == -1 || my_cheapest[set1].weight > current_edge.weight) {
            my_cheapest[set1] = current_edge;
          }

          if (my_cheapest[set2].weight == -1 || my_cheapest[set2].weight > current_edge.weight) {
            my_cheapest[set2] = current_edge;
          }
        }
      }

// Merge local results into global cheapest array
#pragma omp for schedule(auto)
      for (graph_size_t v = 0; v < n_vertices; ++v) {
        for (int t = 0; t < num_threads; ++t) {
          Edge_t *thread_cheapest = &local_cheapest[t * n_vertices];
          if (thread_cheapest[v].weight != -1 &&
              (cheapest[v].weight == -1 || cheapest[v].weight > thread_cheapest[v].weight)) {
            cheapest[v] = thread_cheapest[v];
          }
        }
      }
    }

    // Collect valid candidates first
    n_candidates = 0;
    for (graph_size_t i = 0; i < n_vertices; ++i) {
      if (cheapest[i].weight != -1) {
        Edge_t edge = cheapest[i];
        graph_size_t from = find(subsets, edge.src);
        graph_size_t to = find(subsets, edge.dest);

        if (from != to) {
          candidates[n_candidates++] = edge;
        }
      }
    }

    // Process candidates sequentially to avoid race conditions
    for (graph_size_t i = 0; i < n_candidates && edges_mst < n_vertices - 1; ++i) {
      Edge_t edge = candidates[i];
      graph_size_t from = find(subsets, edge.src);
      graph_size_t to = find(subsets, edge.dest);

      if (from != to) {
        mst->edges[edges_mst++] = edge;
        unionSets(subsets, from, to);
      }
    }
  }

  // Cleanup
  free(base_ptr);
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

  int num_threads = omp_get_max_threads();
  omp_set_num_threads(num_threads);

  double start_time = omp_get_wtime();
  omp_mst(graph, mst);
  double total_time = omp_get_wtime() - start_time;

  if (HPC) {
#pragma omp parallel
    {
#pragma omp master
      {
        printf("omp %s %d %f\n", file_name, omp_get_num_threads(), total_time);
      }
    }
  }

// Compute MST weight in parallel
#pragma omp parallel for reduction(+ : mst_weight) schedule(auto)
  for (graph_size_t i = 0; i < mst->E; i++) {
    mst_weight += mst->edges[i].weight;
  }

  if (!HPC) {
    printf("Total time: %f\n", total_time);
    printf("Total weight of MST: %" PRIu64 "\n", mst_weight);
    log_result("omp", file_name, num_threads, total_time);
  }

  free_graph(mst);
  free_graph(graph);
  return mst_weight;
}
