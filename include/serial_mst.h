#ifndef SERIAL_MST_H
#define SERIAL_MST_H

#include <stdint.h>

#include "common.h"

/** @brief Boruvka's algorithm to find MST
 *  @param graph The input graph
 */
tot_mst_weight_t serial_mst(struct Graph *graph);

/** @brief Run the serial version of Boruvka algorithm
 *  @param argv Array of arguments
 */
tot_mst_weight_t run_serial_mst(int argc, char *argv[]);

#endif  // SERIAL_MST_H
