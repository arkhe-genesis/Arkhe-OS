cmake_minimum_required(VERSION 3.10)
project(arkhe_onnx_cpp)

set(CMAKE_CXX_STANDARD 17)

# Dummy executable
add_library(onnx_executor onnx_executor.cpp)
