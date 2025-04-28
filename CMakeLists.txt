cmake_minimum_required(VERSION 3.10)
project(parallel_mst C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED True)

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

set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS}")
set(CMAKE_C_FLAGS_DEBUG "${CMAKE_C_FLAGS_DEBUG} -g3 -O0 -Wall -Wextra -pedantic") # -Werror
set(CMAKE_C_FLAGS_RELEASE "${CMAKE_C_FLAGS_RELEASE} -O3 -DNDEBUG -w -fPIC")

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

# Add sources
file(GLOB_RECURSE SOURCES ${CMAKE_SOURCE_DIR}/src/*.c)

# Define the executable
add_executable(${PROJECT_NAME} ${SOURCES})

# Link MPI
target_link_libraries(${PROJECT_NAME} MPI::MPI_C)

# Enable Testing
enable_testing()
add_executable(test_all tests/test_mst.c src/serial_mst.c src/common.c src/tools/graph_parser.c)
add_test(NAME MST_Test COMMAND test_all)
