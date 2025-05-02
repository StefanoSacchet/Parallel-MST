cmake_minimum_required(VERSION 3.12)
project(parallel_mst C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED True)

set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS}")
set(CMAKE_C_FLAGS_DEBUG "${CMAKE_C_FLAGS_DEBUG} -g3 -O0 -Wall -Wextra -pedantic") # -Werror
set(CMAKE_C_FLAGS_RELEASE "${CMAKE_C_FLAGS_RELEASE} -O3 -DNDEBUG -w -fPIC")

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

if (APPLE)
  set(CMAKE_C_COMPILER "/opt/homebrew/opt/llvm/bin/clang")
  # set(OPENMP_LIBRARIES "/opt/homebrew/Cellar/llvm/20.1.3/lib")
  # set(OPENMP_INCLUDES "/opt/homebrew/Cellar/llvm/20.1.3/include")
endif()

option(USE_HPC "Enable HPC-specific settings" OFF)
if(USE_HPC)
    message(STATUS "HPC settings enabled")
    add_definitions(-DDATASET_DIR=\"/${CMAKE_CURRENT_SOURCE_DIR}/dataset\")
else()
    message(STATUS "HPC settings disabled")
    add_definitions(-DDATASET_DIR=\"dataset\")
endif()

if(DEFINED RUN_TYPE)
    add_compile_definitions("${RUN_TYPE}")
endif()

# Set output directories
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

# Include directories
include_directories(
  ${CMAKE_SOURCE_DIR}/include
  ${CMAKE_SOURCE_DIR}/include/mpi
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

# Add sources
file(GLOB_RECURSE SOURCES ${CMAKE_SOURCE_DIR}/src/*.c)

# Define the executable
add_executable(${PROJECT_NAME} ${SOURCES})
# Executable for graph generation
add_executable(graph_generator executables/generate_graphs.c src/common.c src/tools/graph_generator.c)

# Link MPI
target_link_libraries(${PROJECT_NAME} MPI::MPI_C)

# Enable Testing
enable_testing()
add_executable(test_all tests/test_mst.c src/serial_mst.c src/mpi/mpi_types.c src/mpi/mpi_mst.c src/tools/logger.c src/common.c src/tools/graph_parser.c)
target_link_libraries(test_all MPI::MPI_C)
add_test(NAME MST_Test COMMAND test_all WORKING_DIRECTORY ${CMAKE_SOURCE_DIR})
