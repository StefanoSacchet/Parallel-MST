cmake_minimum_required(VERSION 3.10)
project(parallel_mst C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED True)

set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Wall -Wextra -Werror -pedantic")

# Debug specific flags
set(CMAKE_C_FLAGS_DEBUG "${CMAKE_C_FLAGS_DEBUG} -g3 -O0")

# Release specific flags
set(CMAKE_C_FLAGS_RELEASE "${CMAKE_C_FLAGS_RELEASE} -O3")

# Set output directories
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

# Include directories
include_directories(${CMAKE_SOURCE_DIR}/include)

# Add sources
set(SOURCES
    src/main.c
    src/serial_mst.c
)

# Define the executable
add_executable(${PROJECT_NAME} ${SOURCES})

# Enable Testing
enable_testing()
add_executable(test_all tests/test_mst.c src/serial_mst.c)
add_test(NAME MST_Test COMMAND test_all)
