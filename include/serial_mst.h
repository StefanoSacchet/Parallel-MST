#ifndef SERIAL_MST_H
#define SERIAL_MST_H

#include <stdint.h>

#include "common.h"

#include <stdint.h>

/** @brief Boruvka's algorithm to find MST
 *  @param graph The input graph
 */
uint64_t serial_mst(struct Graph *graph);

/** @brief Run the serial version of Boruvka algorithm
 *  @param argv Array of arguments
 */
uint64_t run_serial_mst(int argc, char *argv[]);

#endif  // SERIAL_MST_H
