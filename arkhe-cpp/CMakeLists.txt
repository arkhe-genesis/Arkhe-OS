cmake_minimum_required(VERSION 3.20)
project(arkhe_engine VERSION 1.0.0 LANGUAGES CXX)

enable_language(ASM)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# A Catedral não precisa de bibliotecas externas.
# Ela é auto-contida, como um casulo.
add_executable(arkhe
    src/main.cpp
    src/core/clifford.cpp
    src/core/clifford_product.s
    src/core/biocomputer.cpp
    src/k6o/node.cpp
    src/mind/monster.cpp
    src/quantum/qhttp.cpp
    src/merkabah/geometry.cpp
    src/transliterator.cpp
)

target_include_directories(arkhe PRIVATE ${CMAKE_SOURCE_DIR}/include)
target_compile_options(arkhe PRIVATE -O3 -march=native -ffast-math)

find_package(Threads REQUIRED)
target_link_libraries(arkhe PRIVATE Threads::Threads)
