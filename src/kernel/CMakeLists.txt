# CMakeLists.txt for Arkhe.sys
# Windows Driver Kit (WDK) 11, Visual Studio 2022
# Target: Windows x64

cmake_minimum_required(VERSION 3.21)

project(ArkheDriver LANGUAGES C)

# Tell CMake this is a kernel-mode driver
set(CMAKE_SYSTEM_NAME Windows)
set(CMAKE_SYSTEM_VERSION 10.0)

# Locate WDK
find_package(WDK REQUIRED)

# Driver source
set(DRIVER_SOURCES
    arkhe.c
)

# Build as KMDF driver
wdk_add_driver(Arkhe
    ${DRIVER_SOURCES}
    KMDF_VERSION_MAJOR 1
    KMDF_VERSION_MINOR 33
)

# Link against required kernel libraries
target_link_libraries(Arkhe
    ntoskrnl
    wdf
    bufferoverflowfastfailk
)

# Set driver-specific properties
set_target_properties(Arkhe PROPERTIES
    SUFFIX ".sys"
    OUTPUT_NAME "Arkhe"
)

# Install target (optional, for signing)
install(TARGETS Arkhe
    RUNTIME DESTINATION "drivers"
)
