#!/bin/bash
set -e
echo "🔨 Building ARKHE OS ONNX Runtime Polyglot Stack..."

# 1. Rust Secure Loader
echo "📦 Compiling Rust secure loader..."
cd src/rust && cargo build --release && cd ../..

# 2. C++ Native Executor
echo "🔧 Compiling C++ native executor..."
mkdir -p build/cpp && cd build/cpp
cmake ../../src/cpp -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS="-march=native"
make -j$(nproc)
cd ../..

# 3. Python Packages
echo "🐍 Installing Python dependencies..."
pip install -r requirements.txt --quiet

echo "✅ Build complete. Artifacts in build/"
