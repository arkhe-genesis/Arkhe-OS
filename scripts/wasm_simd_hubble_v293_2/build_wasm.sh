#!/bin/bash
# Requer emscripten (emcc) instalado e no PATH
# Exemplo de instalação local:
# git clone https://github.com/emscripten-core/emsdk.git
# cd emsdk && ./emsdk install latest && ./emsdk activate latest && source ./emsdk_env.sh

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

echo "Compiling arkhe_hubble_kernel.cpp to WASM..."

emcc "$DIR/arkhe_hubble_kernel.cpp" -O3 -msimd128 -s EXPORTED_FUNCTIONS="['_compute_global_coherence_matrix', '_malloc', '_free']" -s STANDALONE_WASM --no-entry -o "$DIR/arkhe_hubble_kernel.wasm"

echo "Compilation finished: $DIR/arkhe_hubble_kernel.wasm"
