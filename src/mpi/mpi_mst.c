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

// Define the custom reduction function for finding minimum weight edges
void min_weight_edge_op(void *in, void *inout, int *len, MPI_Datatype *datatype) {
  Edge_t *in_edges = (Edge_t *)in;
  Edge_t *inout_edges = (Edge_t *)inout;
  
  for (int i = 0; i < *len; i++) {
    // If input edge has invalid weight (-1), keep the output edge
    if (in_edges[i].weight == -1) 
      continue;
    
    // If output edge has invalid weight (-1), use input edge
    if (inout_edges[i].weight == -1) {
      inout_edges[i] = in_edges[i];
      continue;
    }
    
    // Otherwise use the edge with minimum weight
    if (in_edges[i].weight < inout_edges[i].weight) {
      inout_edges[i] = in_edges[i];
    }
  }
}

void mpi_mst(Graph_t *graph, Graph_t *mst) {
  int rank, size;
  MPI_Comm_rank(MPI_COMM_WORLD, &rank);
  MPI_Comm_size(MPI_COMM_WORLD, &size);
  MPI_Status status;
  
  // Create custom MPI reduction operation for minimum weight edge
  MPI_Op min_weight_edge_op_handle;
  MPI_Op_create(min_weight_edge_op, 1, &min_weight_edge_op_handle);
  
  // Send number of edges and vertices
  graph_size_t n_edges = 0;
  graph_size_t n_vertices = 0;
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
  
  // Initialize disjoint set
  Subset_t *subsets = (Subset_t *)malloc(n_vertices * sizeof(Subset_t));
  if (subsets == NULL) {
    fprintf(stderr, "Failed to allocate memory for subsets\n");
    MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
  }
  
  // Allocate for MST result on rank 0
  if (rank == 0 && mst != NULL) {
    mst->V = n_vertices;
    mst->E = 0;  // Will be updated as edges are added
    mst->edges = (Edge_t *)realloc(mst->edges, (n_vertices - 1) * sizeof(Edge_t));
    if (mst->edges == NULL) {
      fprintf(stderr, "Failed to allocate memory for MST edges\n");
      MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
    }
  }
  
  graph_size_t edges_mst = 0;
  
  // Cheapest outgoing edge for each component
  Edge_t *cheapest = (Edge_t *)malloc(n_vertices * sizeof(Edge_t));
  Edge_t *global_cheapest = (Edge_t *)malloc(n_vertices * sizeof(Edge_t));
  if (cheapest == NULL || global_cheapest == NULL) {
    fprintf(stderr, "Failed to allocate memory for cheapest edges\n");
    MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
  }
  
  // Initialize subsets and cheapest array
  for (graph_size_t v = 0; v < n_vertices; v++) {
    subsets[v].parent = v;
    subsets[v].rank = 0;
  }

  // Main MST loop - will run at most V-1 times
  while (edges_mst < n_vertices - 1) {
    // Reset cheapest edges array
    for (graph_size_t j = 0; j < n_vertices; j++) {
      cheapest[j].weight = -1;
      global_cheapest[j].weight = -1;
    }
    
    // Find the cheapest outgoing edge for each component in local partition
    for (graph_size_t j = 0; j < edges_per_core; j++) {
      Edge_t current_edge = edges_part[j];
      graph_size_t set1 = find(subsets, current_edge.src);
      graph_size_t set2 = find(subsets, current_edge.dest);
      
      if (set1 != set2) {
        if (cheapest[set1].weight == -1 || current_edge.weight < cheapest[set1].weight) {
          cheapest[set1] = current_edge;
        }
        if (cheapest[set2].weight == -1 || current_edge.weight < cheapest[set2].weight) {
          cheapest[set2] = current_edge;
        }
      }
    }
    
    // Combine cheapest edges from all processes using our custom reduction
    MPI_Allreduce(cheapest, global_cheapest, n_vertices, MPI_EDGE_T, min_weight_edge_op_handle, 
                  MPI_COMM_WORLD);
    
    // Add new edges to MST (all processes update their disjoint sets)
    int new_edges_added = 0;
    for (graph_size_t j = 0; j < n_vertices; j++) {
      if (global_cheapest[j].weight != -1) {
        Edge_t edge = global_cheapest[j];
        graph_size_t set1 = find(subsets, edge.src);
        graph_size_t set2 = find(subsets, edge.dest);
        
        if (set1 != set2) {
          // Add edge to MST on rank 0
          if (rank == 0 && mst != NULL) {
            mst->edges[edges_mst] = edge;
            mst->E++;
          }
          edges_mst++;
          new_edges_added++;
          unionSets(subsets, set1, set2);
        }
      }
    }
    
    // Early termination check - if no new edges were added, we're done
    int global_new_edges;
    MPI_Allreduce(&new_edges_added, &global_new_edges, 1, MPI_INT, MPI_SUM, MPI_COMM_WORLD);
    if (global_new_edges == 0) {
      break;
    }
  }
  
  // Free the custom reduction operation
  MPI_Op_free(&min_weight_edge_op_handle);
  
  // Cleanup
  free(edges_part);
  free(subsets);
  free(cheapest);
  free(global_cheapest);
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
    if (DEBUG)
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

    if (HPC) {
      printf("mpi %s %d %f\n", file_name, size, total_time);
    }

    for (graph_size_t i = 0; i < mst->E; i++) {
      mst_weight += mst->edges[i].weight;
    }

    if (!HPC) {
      /*printf("MST edges: %llu\n", mst->E);*/
      printf("Total time: %f\n", total_time);
      printf("Total weight of MST: %" PRIu64 "\n", mst_weight);
    }

    // Log resutls to file
    if (!HPC)
      log_result("mpi", file_name, size, total_time);

    // Free graph memory
    free_graph(mst);
    free_graph(graph);
  }

  free_mpi_edge_type(&MPI_EDGE_T);
  MPI_Finalize();
  return mst_weight;
}
