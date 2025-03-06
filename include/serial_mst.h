#ifndef SERIAL_MST_H
#define SERIAL_MST_H

#include "common.h"

// Create a graph with V vertices and E edges
struct Graph *create_graph(int V, int E);

// Find set of an element i (uses path compression)
int find(struct Subset subsets[], int i);

// Union of two sets by rank
void unionSets(struct Subset subsets[], int x, int y);

// Boruvka's algorithm to find MST
int boruvkaMST(struct Graph *graph);

#endif  // SERIAL_MST_H
