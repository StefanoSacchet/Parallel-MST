#include <stdio.h>
#include <stdlib.h>

#include "serial_mst.h"

// Create a graph with V vertices and E edges
struct Graph *createGraph(int V, int E) {
    struct Graph *graph = (struct Graph *)malloc(sizeof(struct Graph));
    graph->V = V;
    graph->E = E;
    graph->edge = (struct Edge *)malloc(E * sizeof(struct Edge));
    return graph;
}

// Find set of an element i (uses path compression)
int find(struct Subset subsets[], int i) {
    if (subsets[i].parent != i)
        subsets[i].parent = find(subsets, subsets[i].parent);
    return subsets[i].parent;
}

// Union of two sets by rank
void unionSets(struct Subset subsets[], int x, int y) {
    int rootX = find(subsets, x);
    int rootY = find(subsets, y);

    if (rootX != rootY) {
        if (subsets[rootX].rank < subsets[rootY].rank)
            subsets[rootX].parent = rootY;
        else if (subsets[rootX].rank > subsets[rootY].rank)
            subsets[rootY].parent = rootX;
        else {
            subsets[rootY].parent = rootX;
            subsets[rootX].rank++;
        }
    }
}

// Boruvka's algorithm to find MST
void boruvkaMST(struct Graph *graph) {
    int V = graph->V, E = graph->E;
    struct Edge *edge = graph->edge;
    struct Subset *subsets = (struct Subset *)malloc(V * sizeof(struct Subset));
    int *cheapest = (int *)malloc(V * sizeof(int));

    for (int v = 0; v < V; v++) {
        subsets[v].parent = v;
        subsets[v].rank = 0;
        cheapest[v] = -1;
    }

    int numTrees = V, MSTweight = 0;

    while (numTrees > 1) {
        for (int i = 0; i < V; i++)
            cheapest[i] = -1;

        for (int i = 0; i < E; i++) {
            int set1 = find(subsets, edge[i].src);
            int set2 = find(subsets, edge[i].dest);

            if (set1 != set2) {
                if (cheapest[set1] == -1 || edge[cheapest[set1]].weight > edge[i].weight)
                    cheapest[set1] = i;
                if (cheapest[set2] == -1 || edge[cheapest[set2]].weight > edge[i].weight)
                    cheapest[set2] = i;
            }
        }

        for (int i = 0; i < V; i++) {
            if (cheapest[i] != -1) {
                int set1 = find(subsets, edge[cheapest[i]].src);
                int set2 = find(subsets, edge[cheapest[i]].dest);

                if (set1 != set2) {
                    printf("Edge %d-%d with weight %d included in MST\n", edge[cheapest[i]].src,
                           edge[cheapest[i]].dest, edge[cheapest[i]].weight);
                    MSTweight += edge[cheapest[i]].weight;
                    unionSets(subsets, set1, set2);
                    numTrees--;
                }
            }
        }
    }

    printf("Total weight of MST: %d\n", MSTweight);
    free(subsets);
    free(cheapest);
}
