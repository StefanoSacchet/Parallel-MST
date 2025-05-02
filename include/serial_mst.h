#ifndef SERIAL_MST_H
#define SERIAL_MST_H

#include "common.h"
#include "tools/graph_parser.h"

#include <stdint.h>

/** @brief Boruvka's algorithm to find MST
 *  @param graph The input graph
 */
uint64_t serial_mst(struct Graph *graph);

/** @brief Run the serial version of Boruvka algorithm
 *  @param argv Array of arguments
 */
void run_serial_mst(char *argv[]);

#endif  // SERIAL_MST_H
