#!/bin/bash
# ============================================================
# setup.sh — Download and build llama.cpp
# Usage: ./setup.sh [--cuda] [--metal]
# ============================================================
set -euo pipefail

LLAMA_CPP_PATH="${LLAMA_CPP_PATH:-./llama.cpp}"
BUILD_TYPE="cpu"    # cpu | cuda | metal | vulkan

while [[ $# -gt 0 ]]; do
    case "$1" in
        --cuda)   BUILD_TYPE="cuda"; shift ;;
        --metal)  BUILD_TYPE="metal"; shift ;;
        --vulkan) BUILD_TYPE="vulkan"; shift ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

echo "=== llama.cpp setup (backend: $BUILD_TYPE) ==="

# Clone if not present
if [[ ! -d "$LLAMA_CPP_PATH" ]]; then
    echo "[1/3] Cloning llama.cpp..."
    git clone --depth 1 https://github.com/ggerganov/llama.cpp "$LLAMA_CPP_PATH"
else
    echo "[1/3] llama.cpp already present, pulling latest..."
    git -C "$LLAMA_CPP_PATH" pull --ff-only
fi

# Configure cmake flags
CMAKE_ARGS="-DLLAMA_BUILD_SERVER=ON"
case "$BUILD_TYPE" in
    cuda)   CMAKE_ARGS="$CMAKE_ARGS -DGGML_CUDA=ON" ;;
    metal)  CMAKE_ARGS="$CMAKE_ARGS -DGGML_METAL=ON" ;;
    vulkan) CMAKE_ARGS="$CMAKE_ARGS -DGGML_VULKAN=ON" ;;
esac

# Build
echo "[2/3] Building llama.cpp (this may take a few minutes)..."
cmake -B "$LLAMA_CPP_PATH/build" "$LLAMA_CPP_PATH" $CMAKE_ARGS -DCMAKE_BUILD_TYPE=Release
cmake --build "$LLAMA_CPP_PATH/build" --config Release -j "$(nproc)"

# Verify
SERVER_BIN="$LLAMA_CPP_PATH/build/bin/llama-server"
if [[ -f "$SERVER_BIN" ]]; then
    echo "[3/3] Build successful: $SERVER_BIN"
    "$SERVER_BIN" --version 2>&1 | head -1
else
    echo "[ERROR] Build failed: $SERVER_BIN not found"
    exit 1
fi

mkdir -p models logs

echo ""
echo "=== Setup complete ==="
echo "Next steps:"
echo "  1. Place a .gguf model in ./models/"
echo "     Example: huggingface-cli download bartowski/Meta-Llama-3-8B-Instruct-GGUF --include '*.Q4_K_M.gguf' --local-dir ./models"
echo "  2. Start the server:"
echo "     MODEL_PATH=./models/your-model.gguf ./scripts/server.sh"
