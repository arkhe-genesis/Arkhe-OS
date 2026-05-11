#!/usr/bin/env bash
# scripts/build_wasm.sh — Compilar ARKHE OS para WebAssembly
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
OUTPUT_DIR="${PROJECT_ROOT}/build/wasm/pkg"

echo "🌐 ARKHE OS v168.1 — Compilando para WebAssembly"

# Instalar wasm32 target se necessário
rustup target add wasm32-unknown-unknown 2>/dev/null || true

# Instalar wasm-bindgen CLI se necessário
if ! command -v wasm-bindgen &> /dev/null; then
    echo "📦 Instalando wasm-bindgen..."
    cargo install wasm-bindgen-cli
fi

# Compilar para WASM
echo "🔨 Compilando crate arkhe-wasm..."
cd "${PROJECT_ROOT}/build/wasm"
cargo build --target wasm32-unknown-unknown --release --features "${FEATURES:-nomad}"

# Gerar bindings JavaScript
echo "🔗 Gerando bindings JavaScript..."
wasm-bindgen \
    --out-dir "${OUTPUT_DIR}" \
    --target web \
    --no-typescript \
    "${PROJECT_ROOT}/target/wasm32-unknown-unknown/release/arkhe_wasm.wasm"

# Copiar arquivos auxiliares
cp "${PROJECT_ROOT}/build/wasm/README.md" "${OUTPUT_DIR}/" 2>/dev/null || true
cp "${PROJECT_ROOT}/config/default.yaml" "${OUTPUT_DIR}/config.yaml" 2>/dev/null || true

echo ""
echo "✅ Build WASM concluído!"
echo "📁 Artefatos em: ${OUTPUT_DIR}"
echo ""
echo "🚀 Para usar no navegador:"
echo "  1. Sirva a pasta ${OUTPUT_DIR} com um servidor HTTP"
echo "  2. Importe em seu HTML:"
echo '     <script type="module">'
echo '       import init, { ArkheWasm } from "./arkhe_wasm.js";'
echo '       const arkhe = await init();'
echo '       const orchestrator = new ArkheWasm(config_json);'
echo '       await orchestrator.initialize();'
echo '     </script>'
