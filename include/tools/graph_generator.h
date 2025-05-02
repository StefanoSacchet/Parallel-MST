#ifndef GRAPH_GENERATOR_H
#define GRAPH_GENERATOR_H

#include <stdint.h>

#include "common.h"

void ensure_connectivity(Edge_t *edges, uint64_t num_vertices);
Edge_t *generate_random_graph(uint64_t num_vertices, uint64_t num_edges);
void write_edges_to_file_or_stdout(const char *filename, Edge_t *edges, uint64_t num_edges);

#endif  // !GRAPH_GENERATOR_H
#define GRAPH_GENERATOR_H
