#include <assert.h>
#include <stdio.h>
#include <stdlib.h>

#include "serial_mst.h"

void test_mst(void) {
    int V = 4;  // Number of vertices
    int E = 5;  // Number of edges
    struct Graph *graph = create_graph(V, E);
    graph->edge[0] = (struct Edge){0, 1, 10};
    graph->edge[1] = (struct Edge){0, 2, 6};
    graph->edge[2] = (struct Edge){0, 3, 5};
    graph->edge[3] = (struct Edge){1, 3, 15};
    graph->edge[4] = (struct Edge){2, 3, 4};

    int mst_weight = boruvkaMST(graph);

    free(graph->edge);
    free(graph);

    assert(mst_weight == 19);
}

int main(void) {
    test_mst();
    return 0;
}
