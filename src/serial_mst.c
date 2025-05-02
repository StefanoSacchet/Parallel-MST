#include "serial_mst.h"

#include <stdio.h>
#include <stdlib.h>

#include "graph_parser.h"

// Serial Boruvka's algorithm to find MST
uint64_t serial_mst(struct Graph *graph) {
  int V = graph->V, E = graph->E;
  struct Edge *edge = graph->edges;
  struct Subset *subsets = (struct Subset *)malloc(V * sizeof(struct Subset));
  // Cheapest outgoing edge for each component
  Edge_t *cheapest = (Edge_t *)malloc(V * sizeof(Edge_t));

  // Initialize subsets and cheapest array
  for (int v = 0; v < V; v++) {
    subsets[v].parent = v;
    subsets[v].rank = 0;
    cheapest[v].weight = -1;
  }

  // At the beginning we have V trees
  int edges_mst = 0;
  uint64_t mst_weight = 0;

  // Keep combining components until we have only one tree
  for (int i = 0; i < V && edges_mst < V - 1; i++) {
    // Initialize cheapest array
    for (int i = 0; i < V; i++) {
      cheapest[i].weight = -1;
    }

    // Traverse through all edges and update cheapest of every component
    for (int i = 0; i < E; i++) {
      Edge_t current_edge = edge[i];
      int set1 = find(subsets, current_edge.src);
      int set2 = find(subsets, current_edge.dest);

      if (set1 != set2) {
        if (cheapest[set1].weight == -1 || cheapest[set1].weight > current_edge.weight) {
          cheapest[set1] = current_edge;
        }
        if (cheapest[set2].weight == -1 || cheapest[set2].weight > current_edge.weight) {
          cheapest[set2] = current_edge;
        }
      }
    }

    // Consider the above picked cheapest edges and add them to MST
    for (int i = 0; i < V; i++) {
      // If cheapest for current set exists
      if (cheapest[i].weight != -1) {
        Edge_t edge = cheapest[i];
        int set1 = find(subsets, edge.src);
        int set2 = find(subsets, edge.dest);

        if (set1 != set2) {
          printf("Edge %d-%d with weight %d included in MST\n", edge.src, edge.dest, edge.weight);
          mst_weight += edge.weight;
          edges_mst++;
          unionSets(subsets, set1, set2);
        }
      }
    }
  }

  free(subsets);
  free(cheapest);

  return mst_weight;
}

// Run the serial version of Boruvka algorithm
uint64_t run_serial_mst(int argc, char *argv[]) {
  const char *file_name = argv[argc - 1];

  Graph_t *graph = &(Graph_t){
      .V = 0,
      .E = 0,
      .edges = NULL,
  };

  parse_graph_file(graph, file_name);

  uint64_t mst_weight = serial_mst(graph);
  printf("Total weight of MST: %llu\n", mst_weight);

  free_graph(graph);
  return mst_weight;
}
