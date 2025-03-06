#ifndef COMMON_H
#define COMMON_H

struct Edge {
    int src, dest, weight;
};

struct Graph {
    int V, E;
    struct Edge *edge;
};

// Subset for union-find
struct Subset {
    int parent;
    int rank;
};

#endif  // COMMON_H
