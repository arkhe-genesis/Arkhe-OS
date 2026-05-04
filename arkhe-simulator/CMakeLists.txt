cmake_minimum_required(VERSION 3.16)
project(arkhe_simulator VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable(arkhe-simulator
    src/main.cpp
    src/ontology.cpp
    src/sidecar.cpp
    src/inquisidor.cpp
    src/telemetry.cpp
    src/quantum_vqc.cpp
)

target_include_directories(arkhe-simulator PRIVATE src)

# Para std::this_thread::sleep_for
find_package(Threads REQUIRED)
target_link_libraries(arkhe-simulator Threads::Threads)

# Opções de compilação
if(MSVC)
    target_compile_options(arkhe-simulator PRIVATE /W4)
else()
    target_compile_options(arkhe-simulator PRIVATE -Wall -Wextra -pedantic)
endif()
