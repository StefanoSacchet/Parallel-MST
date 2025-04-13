#include "tools/logger.h"

#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <unistd.h>

#define LOG_DIR "logs"
#define LOG_PATH "logs/results.log"

// Log `input_file`, `num_processes`, `total_time` of the MST algorithm to
// `LOG_PATH` file.
void log_result(const char *file_name, int num_processes, double time) {
  // Create the directory if it does not exist
  if (access(LOG_DIR, F_OK) == -1) {
    // 0755: rwx-rx
    if (mkdir(LOG_DIR, 0755) == -1) {
      fprintf(stderr, "Error creating directory %s\n", LOG_DIR);
      exit(EXIT_FAILURE);
    }
  }

  // If file does not exist, create it and write the header
  if (access(LOG_PATH, F_OK) == -1) {
    FILE *fp = fopen(LOG_PATH, "w");
    if (fp == NULL) {
      fprintf(stderr, "Error creating log file %s\n", LOG_PATH);
      exit(EXIT_FAILURE);
    }
    fprintf(fp, "file_name num_processes Time\n");
    fclose(fp);
  }

  // Append the result to the log file
  FILE *fp = fopen(LOG_PATH, "a");
  if (fp == NULL) {
    fprintf(stderr, "Error opening log file %s for writing\n", LOG_PATH);
    exit(EXIT_FAILURE);
  }

  fprintf(fp, "%s %d %f\n", file_name, num_processes, time);
  fclose(fp);
}
