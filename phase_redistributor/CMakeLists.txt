cmake_minimum_required(VERSION 3.14)
project(PhaseRedistributor)

# Encontrar LibTorch
project(PhaseRedistributor VERSION 1.0.0)

# Compiler flags
set(CMAKE_CXX_STANDARD 17)

# Find required packages
if(NOT DEFINED Torch_DIR)
    set(Torch_DIR /opt/libtorch/share/cmake/Torch)
endif()
find_package(Torch REQUIRED)

add_executable(redistributor_exe src/main.cpp src/PhaseGradientRedistributor.cpp)
target_include_directories(redistributor_exe PRIVATE include)
target_link_libraries(redistributor_exe ${TORCH_LIBRARIES})
set_property(TARGET redistributor_exe PROPERTY CXX_STANDARD 17)
find_package(yaml-cpp REQUIRED)

# Include directories
include_directories(include ${TORCH_INCLUDE_DIRS})

# Main executable (gateway)
add_executable(tzinor_gateway src/gateway_main.cpp src/PhaseGradientRedistributor.cpp)
target_link_libraries(tzinor_gateway ${TORCH_LIBRARIES} yaml-cpp)

# Original redistributor exe (legacy/test)
add_executable(redistributor_exe src/main.cpp src/PhaseGradientRedistributor.cpp)
target_link_libraries(redistributor_exe ${TORCH_LIBRARIES})

# Installation
install(TARGETS tzinor_gateway RUNTIME DESTINATION bin)
