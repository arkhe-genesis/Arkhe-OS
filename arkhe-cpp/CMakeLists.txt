cmake_minimum_required(VERSION 3.10)
project(arkhe-toom)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -mbmi2 -madx")

include_directories(include)

add_library(toom_forge src/toom_forge.cpp src/toom_interpolation.cpp)
add_executable(test_toom src/toom_forge.cpp src/toom_interpolation.cpp)

add_executable(test_arkhe ../tests/test_arkhe_unbuildable_secure.cpp src/arkhe_unbuildable_secure.cpp)
target_link_libraries(test_arkhe dl)
