cmake_minimum_required(VERSION 3.14)
project(PhaseRedistributor)

find_package(Torch REQUIRED)

add_executable(sybil_test src/sybil_test.cpp)
target_include_directories(sybil_test PRIVATE include)
target_link_libraries(sybil_test ${TORCH_LIBRARIES})
set_property(TARGET sybil_test PROPERTY CXX_STANDARD 17)
