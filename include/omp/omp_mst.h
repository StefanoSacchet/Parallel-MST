#ifndef OMP_MST_H
#define OMP_MST_H

#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "common.h"

// Run OpenMP MST
tot_mst_weight_t run_omp_mst(int argc, char *argv[]);
/**
 * @brief Compute the Minimum Spanning Tree (MST) using Borůvka's algorithm with
 * OpenMP.
 *
 * @param `graph` Input graph
 * @param `mst` Output MST graph
 */
void omp_mst(Graph_t *graph, Graph_t *mst);

#endif  // OMP_MST_H
