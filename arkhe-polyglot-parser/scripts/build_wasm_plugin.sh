#!/bin/bash
# Constrói plugin de linguagem como módulo WebAssembly

set -e
PLUGIN_DIR="${1:-templates/language_plugin_wasm}"
OUTPUT_DIR="${2:-dist/plugins}"

echo "🔧 Building Wasm plugin from $PLUGIN_DIR..."

cd "$PLUGIN_DIR"

# Instalar target wasm32-unknown-unknown se necessário
rustup target add wasm32-unknown-unknown 2>/dev/null || true

# Build com otimização
cargo build --release --target wasm32-unknown-unknown

mkdir -p "../../$OUTPUT_DIR"

# Simulating wasm-opt for environments where it's missing
if command -v wasm-opt &> /dev/null; then
    wasm-opt -O4 \
        target/wasm32-unknown-unknown/release/arkhe_language_plugin.wasm \
        -o "../../${OUTPUT_DIR}/mylang_plugin.wasm"
else
    echo "⚠️ wasm-opt not found, simply copying the file."
    cp target/wasm32-unknown-unknown/release/arkhe_language_plugin.wasm "../../${OUTPUT_DIR}/mylang_plugin.wasm"
fi

# Gerar bindings JS se necessário
if command -v wasm-bindgen &> /dev/null; then
    wasm-bindgen \
        --out-dir "../../${OUTPUT_DIR}/js" \
        --target web \
        target/wasm32-unknown-unknown/release/arkhe_language_plugin.wasm
    echo "✅ Plugin built: ${OUTPUT_DIR}/mylang_plugin.wasm"
    echo "   JS bindings: ${OUTPUT_DIR}/js/arkhe_language_plugin.js"
else
    echo "⚠️ wasm-bindgen CLI not found, skipping JS bindings generation."
    echo "✅ Plugin built: ${OUTPUT_DIR}/mylang_plugin.wasm"
fi
