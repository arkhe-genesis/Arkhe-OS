cmake_minimum_required(VERSION 3.22.1)
project(arkhe_native)

set(CMAKE_CXX_STANDARD 17)

add_library(arkhe_core SHARED
    arkhe_core.cpp
    crypto_falcon.cpp
)

target_link_libraries(arkhe_core
    log
)
