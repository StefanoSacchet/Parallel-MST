cmake_minimum_required(VERSION 3.12)
project(parallel_mst C)

# C standard
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED True)

# Compile flags
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS}")
set(CMAKE_C_FLAGS_DEBUG "${CMAKE_C_FLAGS_DEBUG} -g3 -O0 -fopenmp -Wall -Wextra -pedantic")
set(CMAKE_C_FLAGS_RELEASE "${CMAKE_C_FLAGS_RELEASE} -O3 -fopenmp -DNDEBUG -w -fPIC")

# Export compile commands
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Apple-specific config
if (APPLE)
  set(CMAKE_C_COMPILER "/opt/homebrew/opt/llvm/bin/clang")
endif()

# Dataset path
add_definitions(-DDATASET_DIR=\"${CMAKE_CURRENT_SOURCE_DIR}/dataset\")

# HPC optional macro
option(USE_HPC "Enable HPC-specific settings" OFF)
if(USE_HPC)
  message(STATUS "HPC settings enabled")
  add_definitions(-DUSE_HPC)
else()
  message(STATUS "HPC settings disabled")
endif()

# Optional runtime switch
# if(DEFINED RUN_TYPE)
#     add_compile_definitions("${RUN_TYPE}")
# endif()

# Output directories
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

# Include directories
include_directories(
  ${CMAKE_SOURCE_DIR}/include
  ${CMAKE_SOURCE_DIR}/include/mpi
  ${CMAKE_SOURCE_DIR}/include/omp
  ${CMAKE_SOURCE_DIR}/include/hybrid
  ${CMAKE_SOURCE_DIR}/include/tools
)

# Find MPI
find_package(MPI REQUIRED)
include_directories(${MPI_INCLUDE_PATH})

# Find OpenMP
if(APPLE AND CMAKE_C_COMPILER_ID MATCHES "Clang")
  set(OpenMP_C "${CMAKE_C_COMPILER}")
  set(OpenMP_C_FLAGS "-fopenmp=libomp -Wno-unused-command-line-argument")
  set(OpenMP_C_LIB_NAMES "libomp" "libgomp" "libiomp5")
  set(OpenMP_libomp_LIBRARY ${OpenMP_C_LIB_NAMES})
  set(OpenMP_libgomp_LIBRARY ${OpenMP_C_LIB_NAMES})
  set(OpenMP_libiomp5_LIBRARY ${OpenMP_C_LIB_NAMES})
endif()
find_package(OpenMP REQUIRED)
if (OPENMP_FOUND)
  # include_directories("${OPENMP_INCLUDES}")
  # link_directories("${OPENMP_LIBRARIES}")
  set (CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${OpenMP_C_FLAGS}")
  # set (CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} ${OpenMP_EXE_LINKER_FLAGS}")
endif(OPENMP_FOUND)

# Gather source files
file(GLOB_RECURSE COMMON_SOURCES ${CMAKE_SOURCE_DIR}/src/common.c)
file(GLOB_RECURSE SERIAL_SOURCES ${CMAKE_SOURCE_DIR}/src/serial_mst.c)
file(GLOB_RECURSE MPI_SOURCES ${CMAKE_SOURCE_DIR}/src/mpi/*.c)
file(GLOB_RECURSE OMP_SOURCES ${CMAKE_SOURCE_DIR}/src/omp/*.c)
file(GLOB_RECURSE HYBRID_SOURCES ${CMAKE_SOURCE_DIR}/src/hybrid/*.c)
file(GLOB_RECURSE TOOL_SOURCES ${CMAKE_SOURCE_DIR}/src/tools/*.c)

# --- Executables ---

string(TOLOWER "${RUN_TYPE}" RUN_TYPE_LOWER)

# Define flags for which executable(s) to build
set(BUILD_SERIAL_MST OFF)
set(BUILD_MPI_MST OFF)
set(BUILD_OMP_MST OFF)
set(BUILD_HYBRID_MST OFF)
set(BUILD_GRAPH_GENERATOR ON)
set(BUILD_TESTS OFF)

if(RUN_TYPE_LOWER STREQUAL "all")
  set(BUILD_SERIAL_MST ON)
  set(BUILD_MPI_MST ON)
  set(BUILD_OMP_MST ON)
  set(BUILD_HYBRID_MST ON)
  set(BUILD_GRAPH_GENERATOR ON)
  set(BUILD_TESTS ON)
elseif(RUN_TYPE_LOWER STREQUAL "mpi")
  set(BUILD_MPI_MST ON)
elseif(RUN_TYPE_LOWER STREQUAL "omp")
  set(BUILD_OMP_MST ON)
elseif(RUN_TYPE_LOWER STREQUAL "hybrid")
  set(BUILD_HYBRID_MST ON)
elseif(RUN_TYPE_LOWER STREQUAL "serial")
  set(BUILD_SERIAL_MST ON)
elseif(RUN_TYPE_LOWER STREQUAL "graph_gen")
  set(BUILD_GRAPH_GENERATOR ON)
elseif(RUN_TYPE_LOWER STREQUAL "tests")
  set(BUILD_TESTS ON)
  set(BUILD_SERIAL_MST ON)  # Tests require the serial MST implementation
  set(BUILD_MPI_MST ON)     # Tests require the MPI implementation
  set(BUILD_OMP_MST ON)     # Tests require the OpenMP implementation
  set(BUILD_HYBRID_MST ON)  # Tests require the hybrid implementation
else()
  message(FATAL_ERROR "Invalid RUN_TYPE: ${RUN_TYPE}.")
endif()

# Serial executable
if(BUILD_SERIAL_MST)
  add_executable(serial_mst executables/main.c ${COMMON_SOURCES} ${TOOL_SOURCES} ${SERIAL_SOURCES})
  target_compile_definitions(serial_mst PRIVATE SERIAL)
endif()

# MPI executable
if(BUILD_MPI_MST)
  add_executable(mpi_mst executables/main.c ${COMMON_SOURCES} ${TOOL_SOURCES} ${MPI_SOURCES})
  target_link_libraries(mpi_mst MPI::MPI_C)
  target_compile_definitions(mpi_mst PRIVATE MPI)
endif()

# OMP executable
if(BUILD_OMP_MST)
  add_executable(omp_mst executables/main.c ${COMMON_SOURCES} ${TOOL_SOURCES} ${OMP_SOURCES})
  target_compile_definitions(omp_mst PRIVATE OMP)
endif()

# Hybrid executable (MPI + OMP)
if(BUILD_HYBRID_MST)
  add_executable(hybrid_mst executables/main.c ${COMMON_SOURCES} ${TOOL_SOURCES} ${HYBRID_SOURCES})
  target_link_libraries(hybrid_mst MPI::MPI_C)
  target_compile_definitions(hybrid_mst PRIVATE HYBRID)
endif()

# Graph generator (always built)
if(BUILD_GRAPH_GENERATOR)
  add_executable(graph_generator executables/generate_graphs.c ${COMMON_SOURCES} ${TOOL_SOURCES})
endif()

# --- Tests ---

if(BUILD_TESTS)
  enable_testing()
  add_executable(test_all tests/test_mst.c ${COMMON_SOURCES} ${TOOL_SOURCES} ${SERIAL_SOURCES} ${MPI_SOURCES})
  target_link_libraries(test_all MPI::MPI_C)

  add_test(NAME test_serial_mst COMMAND test_all test_serial_mst WORKING_DIRECTORY ${CMAKE_SOURCE_DIR})
  add_test(NAME test_mpi_vs_serial COMMAND test_all test_mpi_vs_serial WORKING_DIRECTORY ${CMAKE_SOURCE_DIR})
  add_test(NAME test_mpi_vs_serial_2 COMMAND test_all test_mpi_vs_serial_2 WORKING_DIRECTORY ${CMAKE_SOURCE_DIR})
endif()
