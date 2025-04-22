#include "mpi_mst.h"

#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>

#include "logger.h"
#include "mpi_types.h"
#include "tools/graph_parser.h"

static MPI_Datatype MPI_EDGE_T;
static int rank, size;

/** @brief Dispatch edges to all processes
 *  @param edges The list containing all edges
 *  @param edges_part The list containing the edges for this process
 *  @param n_edges The number of edges in the graph
 *  @param edges_per_core The number of edges per core
 */
void scatter_edge_list(Edge_t *edges, Edge_t *edges_part, const int n_edges, int *edges_per_core) {
  MPI_Scatter(edges, *edges_per_core, MPI_EDGE_T, edges_part, *edges_per_core, MPI_EDGE_T, 0,
              MPI_COMM_WORLD);

  // Calculate reminder for last process
  if (rank == size - 1 && n_edges % *edges_per_core != 0) {
    *edges_per_core = n_edges % *edges_per_core;
  }
}

void mpi_mst(struct Graph *graph, struct Graph *mst) {
  MPI_Comm_rank(MPI_COMM_WORLD, &rank);
  MPI_Comm_size(MPI_COMM_WORLD, &size);
  MPI_Status status;

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

  // init set
  Subset_t *subsets = (Subset_t *)malloc(n_vertices * sizeof(Subset_t));

  int edges_mst = 0;
  // Cheapest outgoing edge for each component
  Edge_t *cheapest = (Edge_t *)malloc(n_vertices * sizeof(Edge_t));
	Edge_t* cheapest_edge_received = (Edge_t*)malloc(n_vertices * sizeof(Edge_t));

  // Initialize subsets and cheapest array
  for (int v = 0; v < n_vertices; v++) {
    subsets[v].parent = v;
    subsets[v].rank = 0;
    cheapest[v].weight = -1;
  }

  for (int i = 0; i < n_vertices && edges_mst < n_vertices - 1; i++) {
    // reset cheapest edges array
    for (int j = 0; j < n_vertices; j++) {
      cheapest[j].weight = -1;
    }

    // Traverse through all edges and update cheapest of every component
    for (int j = 0; j < edges_per_core; j++) {
      Edge_t current_edge = edges_part[j];
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

    int from;
    int to;
    for (int step = 1; step < size; step *= 2) {
      if (rank % (2 * step) == 0) {
        from = rank + step;
        if (from < size) {
          MPI_Recv(cheapest_edge_received, n_vertices, MPI_EDGE_T, from, 0, MPI_COMM_WORLD, &status);

          // combine cheapest edges
          for (int j = 0; j < n_vertices; j++) {
            // int current_vertex = j;
            if (cheapest_edge_received[j].weight != -1 && (cheapest[j].weight == -1 || cheapest_edge_received[j].weight < cheapest[j].weight)) {
              cheapest[j] = cheapest_edge_received[j];
            }
          }
        }
      } else if (rank % step == 0) {
        to = rank - step;
        MPI_Send(cheapest, n_vertices, MPI_EDGE_T, to, 0, MPI_COMM_WORLD);
      }
    }
    MPI_Bcast(cheapest, n_vertices, MPI_EDGE_T, 0, MPI_COMM_WORLD);

    // add new edges to MST
    for (int j = 0; j < n_vertices; j++) {
      if (cheapest[j].weight != -1) {

        Edge_t edge = cheapest[j];
        
        int from = find(subsets, edge.src);
        int to = find(subsets, edge.dest);
      
        if (from != to) {
          if (rank == 0) {
            mst->edges[edges_mst] = edge;
            printf("Edge %d-%d with weight %d included in MST\n", edge.src,
              edge.dest, edge.weight);
            }
            edges_mst++;
          }
          unionSets(subsets, from, to);
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
void run_mpi_mst(int argc, char *argv[]) {
  const char *file_name = argv[1];

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
    
    unsigned long mst_weight = 0;
		for (int i = 0; i < mst->E; i++) {
      mst_weight += mst->edges[i].weight;
		}

    printf("MST edges: %d\n", mst->E);
    
    printf("Total weight of MST: %lu\n", mst_weight);
    // Log resutls to file
    log_result(file_name, size, total_time);

    // Free graph memory
    free_graph(mst);
    free_graph(graph);
  }

  free_mpi_edge_type(&MPI_EDGE_T);
  MPI_Finalize();
}
