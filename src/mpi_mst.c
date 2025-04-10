#include "mpi_mst.h"

#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>

#include "common.h"

void scatterEdgeList(Edge_t *edges, Edge_t *edges_part, const int n_edges, int *edges_per_core) {
  int rank, size;
  MPI_Comm_rank(MPI_COMM_WORLD, &rank);
  MPI_Comm_size(MPI_COMM_WORLD, &size);

  MPI_Scatter(edges, *edges_per_core, MPI_EDGE_T, edges_part, *edges_per_core, MPI_EDGE_T, 0,
              MPI_COMM_WORLD);

  // Calculate reminder for last process
  if (rank == size - 1 && n_edges % *edges_per_core != 0) {
    *edges_per_core = n_edges % *edges_per_core;
  }
}

int mpi_mst(struct Graph *graph, struct Graph *mst) {
  int rank, size;
  MPI_Comm_rank(MPI_COMM_WORLD, &rank);
  MPI_Comm_size(MPI_COMM_WORLD, &size);

  // Send number of edges and vertices
  int n_edges;
  int n_vertices;
  if (rank == 0) {
    n_edges = graph->E;
    n_vertices = graph->V;
    MPI_Bcast(&n_edges, 1, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Bcast(&n_vertices, 1, MPI_INT, 0, MPI_COMM_WORLD);
  } else {
    MPI_Bcast(&n_edges, 1, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Bcast(&n_vertices, 1, MPI_INT, 0, MPI_COMM_WORLD);
  }

  // scatter the edges to search in them
  int edges_per_core = (n_edges + size - 1) / size;
  Edge_t *edges_part = (Edge_t *)malloc(edges_per_core * sizeof(Edge_t));
  scatterEdgeList(graph->edges, edges_part, n_edges, &edges_per_core);
}

void run_mpi_mst(int argc, char *argv[]) {
  int rank, size;

  // Custom types
  int blocklengths[3];
  MPI_Aint offsets[3];

  MPI_Init(&argc, &argv);
  MPI_Comm_rank(MPI_COMM_WORLD, &rank);
  MPI_Comm_size(MPI_COMM_WORLD, &size);

  // Field src
  offsets[0] = offsetof(Edge_t, src);
  oldtypes[0] = MPI_INT;
  blocklengths[0] = 1;

  // Field dest
  offsets[1] = offsetof(Edge_t, dest);
  oldtypes[1] = MPI_INT;
  blocklengths[1] = 1;

  // Field weight
  offsets[2] = offsetof(Edge_t, weight);
  oldtypes[2] = MPI_INT;
  blocklengths[2] = 1;

  MPI_Type_create_struct(3, blocklengths, offsets, oldtypes, &MPI_EDGE_T);
  MPI_Type_commit(&MPI_EDGE_T);

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

  double start = 0;

  if (rank == 0) {
    int V = 4;  // Number of vertices
    int E = 5;  // Number of edges
    graph = create_graph(V, E);

    graph->edges[0] = (struct Edge){0, 1, 10};
    graph->edges[1] = (struct Edge){0, 2, 6};
    graph->edges[2] = (struct Edge){0, 3, 5};
    graph->edges[3] = (struct Edge){1, 3, 15};
    graph->edges[4] = (struct Edge){2, 3, 4};

    start = MPI_Wtime();
  }

  // If number of processes is much greater than number of edges
  if (graph->E / 3 < size && graph->E != size) {
    if (rank == 0) {
      fprintf(stderr, "Too many processes compared to edges!\n");
    }
    MPI_Finalize();
    exit(EXIT_FAILURE);
  }

  int mst_weight = mpi_mst(graph, mst);

  if (rank == 0) {
    double end = MPI_Wtime();
    printf("Total time: %f\n", end - start);
    printf("Total weight of MST: %d\n", mst_weight);
  }

  MPI_Type_free(&MPI_EDGE_T);
  MPI_Finalize();
}
