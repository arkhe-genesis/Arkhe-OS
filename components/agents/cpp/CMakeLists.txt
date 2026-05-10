cmake_minimum_required(VERSION 3.10)
project(arkhe_agent_cpp)

set(CMAKE_CXX_STANDARD 17)

include(FetchContent)
FetchContent_Declare(json URL https://github.com/nlohmann/json/releases/download/v3.11.2/json.tar.xz)
FetchContent_MakeAvailable(json)

add_executable(arkhe_agent_cpp arkhe_agent_cpp.cpp)
target_link_libraries(arkhe_agent_cpp PRIVATE nlohmann_json::nlohmann_json)
