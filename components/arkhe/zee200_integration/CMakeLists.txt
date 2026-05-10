cmake_minimum_required(VERSION 3.15)
project(zee200_backend LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Encontrar pybind11
find_package(pybind11 REQUIRED)

# Paths para headers do ZEE200 (assumindo checkout paralelo)
set(ZEE200_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../ZEE200")
include_directories(
    ${ZEE200_ROOT}/include
    ${ZEE200_ROOT}/external/emp-tool/include
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Bibliotecas do ZEE200 a linkar
set(ZEE200_LIBS
    ${ZEE200_ROOT}/build/lib/libgtzk_cpu.a
    ${ZEE200_ROOT}/build/lib/libemp_zk.a
    ${ZEE200_ROOT}/build/lib/libemp_ot.a
)

# Módulo pybind11 principal
pybind11_add_module(zee200_backend zee200_bindings.cpp)

target_link_libraries(zee200_backend PRIVATE ${ZEE200_LIBS})
target_compile_definitions(zee200_backend PRIVATE
    FIELD_MERSENNE_61  # Usar F_{2^61-1}
    SECURITY_BITS=40   # Default para testes rápidos
)

# Instalar para site-packages do Python
install(TARGETS zee200_backend LIBRARY DESTINATION .)
