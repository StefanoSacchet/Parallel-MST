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

// Create a graph with V vertices and E edges
struct Graph *create_graph(int V, int E);

// Find set of an element i (uses path compression)
int find(struct Subset subsets[], int i);

// Union of two sets by rank
void unionSets(struct Subset subsets[], int x, int y);

// Boruvka's algorithm to find MST
int boruvkaMST(struct Graph *graph);
