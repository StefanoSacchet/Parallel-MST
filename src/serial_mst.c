#include "serial_mst.h"

#include <stdio.h>
#include <stdlib.h>

// Boruvka's algorithm to find MST
int boruvkaMST(struct Graph *graph) {
  int V = graph->V, E = graph->E;
  struct Edge *edge = graph->edges;
  struct Subset *subsets = (struct Subset *)malloc(V * sizeof(struct Subset));
  // Cheapest outgoing edge for each component
  int *cheapest = (int *)malloc(V * sizeof(int));

  // Initialize subsets and cheapest array
  for (int v = 0; v < V; v++) {
    subsets[v].parent = v;
    subsets[v].rank = 0;
    cheapest[v] = -1;
  }

  // At the beginning we have V trees
  int num_trees = V, mst_weight = 0;

  // Keep combining components until we have only one tree
  while (num_trees > 1) {
    // Initialize cheapest array
    for (int i = 0; i < V; i++) {
      cheapest[i] = -1;
    }

    // Traverse through all edges and update cheapest of every component
    for (int i = 0; i < E; i++) {
      int set1 = find(subsets, edge[i].src);
      int set2 = find(subsets, edge[i].dest);

      if (set1 != set2) {
        if (cheapest[set1] == -1 || edge[cheapest[set1]].weight > edge[i].weight) {
          cheapest[set1] = i;
        }
        if (cheapest[set2] == -1 || edge[cheapest[set2]].weight > edge[i].weight) {
          cheapest[set2] = i;
        }
      }
    }

    for (int k = 0; k < V; k++) {
      printf("cheapest[%d] = %d\n", k, cheapest[k]);  
    }

    // Consider the above picked cheapest edges and add them to MST
    for (int i = 0; i < V; i++) {
      // If cheapest for current set exists
      if (cheapest[i] != -1) {
        int set1 = find(subsets, edge[cheapest[i]].src);
        int set2 = find(subsets, edge[cheapest[i]].dest);

        if (set1 != set2) {
          printf("Edge %d-%d with weight %d included in MST\n", edge[cheapest[i]].src,
                 edge[cheapest[i]].dest, edge[cheapest[i]].weight);
          mst_weight += edge[cheapest[i]].weight;
          unionSets(subsets, set1, set2);
          num_trees--;
        }
      }
    }
  }

  free(subsets);
  free(cheapest);

  return mst_weight;
}
