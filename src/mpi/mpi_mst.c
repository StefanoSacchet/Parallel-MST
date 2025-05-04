#include "mpi_mst.h"

#include <assert.h>
#include <limits.h>
#include <mpi.h>
#include <stdbool.h>
#include <stdlib.h>

#include "common.h"
#include "logger.h"
#include "mpi_types.h"
#include "tools/graph_parser.h"

static MPI_Datatype MPI_EDGE_T;
static int rank, size;

void scatter_edge_list(Edge_t *edges, Edge_t **edges_part_ptr, const graph_size_t n_edges,
                       graph_size_t *edges_per_core, int rank, int size) {
  // Calculate base edges per core and remainder
  *edges_per_core = n_edges / size;
  graph_size_t remainder = n_edges % size;

  // Last process gets the remainder
  graph_size_t recv_count = *edges_per_core + (rank == size - 1 ? remainder : 0);

  // Reallocate memory if needed (safely handles NULL input)
  *edges_part_ptr = (Edge_t *)realloc(*edges_part_ptr, recv_count * sizeof(Edge_t));
  if (*edges_part_ptr == NULL && recv_count > 0) {
    fprintf(stderr, "Failed to allocate memory for edges part\n");
    MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
  }

  // Prepare send counts and displacements for uneven distribution
  int *send_counts = NULL;
  int *displs = NULL;

  if (rank == 0) {
    send_counts = (int *)malloc(size * sizeof(int));
    displs = (int *)malloc(size * sizeof(int));
    if (send_counts == NULL || displs == NULL) {
      fprintf(stderr, "Failed to allocate memory for send counts or displacements\n");
      MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
    }

    graph_size_t offset = 0;
    for (int i = 0; i < size; i++) {
      graph_size_t count = *edges_per_core + (i == size - 1 ? remainder : 0);
      if (count > INT_MAX || offset > INT_MAX) {
        fprintf(stderr, "Overflow detected in edge scatter\n");
        MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
      }
      send_counts[i] = (int)count;
      displs[i] = (int)offset;
      offset += count;
    }
  }

  // Use MPI_Scatterv for uneven distribution
  MPI_Scatterv(edges, send_counts, displs, MPI_EDGE_T, *edges_part_ptr, recv_count, MPI_EDGE_T, 0,
               MPI_COMM_WORLD);

  if (rank == 0) {
    free(send_counts);
    free(displs);
  }

  // Update edges_per_core to actual received count
  *edges_per_core = recv_count;
}

void mpi_mst(struct Graph *graph, struct Graph *mst) {
  MPI_Comm_rank(MPI_COMM_WORLD, &rank);
  MPI_Comm_size(MPI_COMM_WORLD, &size);
  MPI_Status status;

  // Send number of edges and vertices
  graph_size_t n_edges;
  graph_size_t n_vertices;
  if (rank == 0) {
    n_edges = graph->E;
    n_vertices = graph->V;
  }

  MPI_Bcast(&n_edges, 1, MPI_GRAPH_SIZE_T, 0, MPI_COMM_WORLD);
  MPI_Bcast(&n_vertices, 1, MPI_GRAPH_SIZE_T, 0, MPI_COMM_WORLD);

  // Scatter the edges to search in them
  graph_size_t edges_per_core = 0;
  Edge_t *edges_part = NULL;
  scatter_edge_list(graph->edges, &edges_part, n_edges, &edges_per_core, rank, size);

  // Init set
  Subset_t *subsets = (Subset_t *)malloc(n_vertices * sizeof(Subset_t));
  if (subsets == NULL) {
    fprintf(stderr, "Failed to allocate memory for subsets\n");
    MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
  }

  graph_size_t edges_mst = 0;

  // Cheapest outgoing edge for each component
  Edge_t *cheapest = (Edge_t *)malloc(n_vertices * sizeof(Edge_t));
  Edge_t *cheapest_edge_received = (Edge_t *)malloc(n_vertices * sizeof(Edge_t));
  if (cheapest == NULL || cheapest_edge_received == NULL) {
    fprintf(stderr, "Failed to allocate memory for cheapest edges\n");
    MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
  }

  // Initialize subsets and cheapest array
  for (graph_size_t v = 0; v < n_vertices; v++) {
    subsets[v].parent = v;
    subsets[v].rank = 0;
    cheapest[v].weight = -1;
  }

  for (graph_size_t i = 0; i < n_vertices && edges_mst < n_vertices - 1; i++) {
    // Reset cheapest edges array
    for (graph_size_t j = 0; j < n_vertices; j++) {
      cheapest[j].weight = -1;
    }

    // Traverse through all edges and update cheapest of every component
    for (graph_size_t j = 0; j < edges_per_core; j++) {
      Edge_t current_edge = edges_part[j];
      graph_size_t set1 = find(subsets, current_edge.src);
      graph_size_t set2 = find(subsets, current_edge.dest);

      if (set1 != set2) {
        if (cheapest[set1].weight == -1 || cheapest[set1].weight > current_edge.weight) {
          cheapest[set1] = current_edge;
        }
        if (cheapest[set2].weight == -1 || cheapest[set2].weight > current_edge.weight) {
          cheapest[set2] = current_edge;
        }
      }
    }

    int from, to;
    for (int step = 1; step < size; step *= 2) {
      if (rank % (2 * step) == 0) {
        from = rank + step;
        if (from < size) {
          assert(n_vertices <= INT_MAX);
          MPI_Recv(cheapest_edge_received, (int)n_vertices, MPI_EDGE_T, from, 0, MPI_COMM_WORLD,
                   &status);

          for (graph_size_t j = 0; j < n_vertices; j++) {
            if (cheapest_edge_received[j].weight != -1 &&
                (cheapest[j].weight == -1 ||
                 cheapest_edge_received[j].weight < cheapest[j].weight)) {
              cheapest[j] = cheapest_edge_received[j];
            }
          }
        }
      } else if (rank % step == 0) {
        to = rank - step;
        assert(n_vertices <= INT_MAX);
        MPI_Send(cheapest, (int)n_vertices, MPI_EDGE_T, to, 0, MPI_COMM_WORLD);
      }
    }

    assert(n_vertices <= INT_MAX);
    MPI_Bcast(cheapest, (int)n_vertices, MPI_EDGE_T, 0, MPI_COMM_WORLD);

    // Add new edges to MST
    for (graph_size_t j = 0; j < n_vertices; j++) {
      if (cheapest[j].weight != -1) {
        Edge_t edge = cheapest[j];

        graph_size_t from = find(subsets, edge.src);
        graph_size_t to = find(subsets, edge.dest);

        if (from != to) {
          if (rank == 0) {
            mst->edges[edges_mst] = edge;
          }
          edges_mst++;
          unionSets(subsets, from, to);
        }
      }
    }
  }

  free(edges_part);
  free(subsets);
  free(cheapest);
  free(cheapest_edge_received);
}

/** @brief Run the parallel version of Boruvka algorithm using MPI
 *  @param argc Number of arguments
 *  @param argv Array of arguments
 */
tot_mst_weight_t run_mpi_mst(int argc, char *argv[]) {
  const char *file_name = argv[argc - 1];
  tot_mst_weight_t mst_weight = 0;

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
    printf("Running in MPI mode\n");
    parse_graph_file(graph, file_name);
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

  mpi_mst(graph, mst);

  if (rank == 0) {
    double total_time = MPI_Wtime() - start_time;
    printf("Total time: %f\n", total_time);

    for (graph_size_t i = 0; i < mst->E; i++) {
      mst_weight += mst->edges[i].weight;
    }

    printf("MST edges: %llu\n", mst->E);
    printf("Total weight of MST: %llu\n", mst_weight);

    // Log resutls to file
    log_result(file_name, size, total_time);

    // Free graph memory
    free_graph(mst);
    free_graph(graph);
  }

  free_mpi_edge_type(&MPI_EDGE_T);
  MPI_Finalize();
  return mst_weight;
}
