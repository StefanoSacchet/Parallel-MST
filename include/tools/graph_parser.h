#ifndef GRAPH_PARSER_H
#define GRAPH_PARSER_H

#include "common.h"

// Parse `filename` graph file and populate the `graph` structure.
void parse_graph_file(Graph_t *graph, const char *filename);

#endif  // GRAPH_PARSER_H
