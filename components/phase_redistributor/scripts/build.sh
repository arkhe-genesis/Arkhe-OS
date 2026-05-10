#!/bin/bash
# build.sh – Build PhaseGradientRedistributor components

set -e  # exit on error

# ------------------------------
# Configuration
# ------------------------------
BUILD_DIR="build"
INSTALL_PREFIX="/usr/local"
LIBTORCH_PATH="/opt/libtorch"          # Default for Arkhe-PNT environment
NUM_THREADS=$(nproc)

# Optional: cross‑compile for ARM64 (Raspberry Pi)
CROSS_COMPILE_ARM=false
ARM_TOOLCHAIN_FILE=""
if [[ "$1" == "--arm64" ]]; then
    CROSS_COMPILE_ARM=true
    echo "Cross‑compiling for ARM64 (Raspberry Pi)"
fi

# ------------------------------
# Setup LibTorch environment
# ------------------------------
if [ ! -d "$LIBTORCH_PATH" ]; then
    echo "Error: LibTorch not found at $LIBTORCH_PATH"
    echo "Please ensure LibTorch is installed in $LIBTORCH_PATH"
    exit 1
fi

export CMAKE_PREFIX_PATH="$LIBTORCH_PATH"

# ------------------------------
# Create build directory
# ------------------------------
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# ------------------------------
# Configure CMake
# ------------------------------
CMAKE_ARGS=(
    -DCMAKE_PREFIX_PATH="$LIBTORCH_PATH"
    -DCMAKE_INSTALL_PREFIX="$INSTALL_PREFIX"
    -DCMAKE_BUILD_TYPE=Release
)

if [ "$CROSS_COMPILE_ARM" = true ]; then
    # Set cross‑compilation toolchain
    export CC=aarch64-linux-gnu-gcc
    export CXX=aarch64-linux-gnu-g++
    CMAKE_ARGS+=(
        -DCMAKE_SYSTEM_NAME=Linux
        -DCMAKE_SYSTEM_PROCESSOR=aarch64
        -DCMAKE_C_COMPILER=aarch64-linux-gnu-gcc
        -DCMAKE_CXX_COMPILER=aarch64-linux-gnu-g++
    )
    if [ -n "$ARM_TOOLCHAIN_FILE" ]; then
        CMAKE_ARGS+=(-DCMAKE_TOOLCHAIN_FILE="$ARM_TOOLCHAIN_FILE")
    fi
fi

cmake .. "${CMAKE_ARGS[@]}"

# ------------------------------
# Compile
# ------------------------------
make -j"$NUM_THREADS"

echo "Build completed successfully."
