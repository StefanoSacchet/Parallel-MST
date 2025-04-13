#include "mpi_mst.h"

#include <stdlib.h>

#include "mpi_types.h"
#include "tools/graph_parser.h"

static MPI_Datatype MPI_EDGE_T;
static int rank, size;

void scatter_edge_list(Edge_t *edges, Edge_t *edges_part, const int n_edges, int *edges_per_core) {
  MPI_Scatter(edges, *edges_per_core, MPI_EDGE_T, edges_part, *edges_per_core, MPI_EDGE_T, 0,
              MPI_COMM_WORLD);

  // Calculate reminder for last process
  if (rank == size - 1 && n_edges % *edges_per_core != 0) {
    *edges_per_core = n_edges % *edges_per_core;
  }
}

uint64_t mpi_mst(struct Graph *graph, struct Graph *mst) {
  MPI_Comm_rank(MPI_COMM_WORLD, &rank);
  MPI_Comm_size(MPI_COMM_WORLD, &size);

  // Send number of edges and vertices
  int n_edges;
  int n_vertices;
  if (rank == 0) {
    n_edges = graph->E;
    n_vertices = graph->V;
  }
  MPI_Bcast(&n_edges, 1, MPI_INT, 0, MPI_COMM_WORLD);
  MPI_Bcast(&n_vertices, 1, MPI_INT, 0, MPI_COMM_WORLD);

  // scatter the edges to search in them
  int edges_per_core = (n_edges + size - 1) / size;
  Edge_t *edges_part = (Edge_t *)malloc(edges_per_core * sizeof(Edge_t));
  scatter_edge_list(graph->edges, edges_part, n_edges, &edges_per_core);

  return 0;
}

void run_mpi_mst(int argc, char *argv[]) {
  MPI_Init(&argc, &argv);
  MPI_Comm_rank(MPI_COMM_WORLD, &rank);
  MPI_Comm_size(MPI_COMM_WORLD, &size);

  create_mpi_edge_type(&MPI_EDGE_T);

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

  double start_time = 0;

  if (rank == 0) {
    parse_graph_file(graph, argv[1]);
    init_graph(mst, graph->V, graph->V - 1);
    start_time = MPI_Wtime();
  }

  // If number of processes is much greater than number of edges
  /*if (graph->E / 3 < size && graph->E != size) {*/
  /*  if (rank == 0) {*/
  /*    fprintf(stderr, "Too many processes compared to edges!\n");*/
  /*  }*/
  /*  MPI_Finalize();*/
  /*  exit(EXIT_FAILURE);*/
  /*}*/

  u_int64_t mst_weight = mpi_mst(graph, mst);

  if (rank == 0) {
    double end = MPI_Wtime();
    printf("Total time: %f\n", end - start_time);
    printf("Total weight of MST: %llu\n", mst_weight);

    // Free graph memory
    free_graph(mst);
    free_graph(graph);
  }

  free_mpi_edge_type(&MPI_EDGE_T);
  MPI_Finalize();
}
