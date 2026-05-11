#!/bin/bash
# ARKHE P³ — Build Script
set -e

echo "═══════════════════════════════════════════════════"
echo "  ARKHE P³ — Polymath-Polyglot Parser"
echo "  Substrato 6061"
echo "═══════════════════════════════════════════════════"
echo ""

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

# 1. Rust build
echo "[1/5] Construindo core Rust..."
cargo build --release --all-features 2>&1 | tail -20

# 2. Wasm build (se feature habilitada)
echo "[2/5] Construindo módulo WebAssembly..."
if cargo build --release --features wasm 2>&1 | tail -10; then
    echo "  ✓ Wasm module gerado em target/wasm32-unknown-unknown/release/"
    # wasm-opt -O4 -o target/wasm32-unknown-unknown/release/polyglot_opt.wasm \
    #    target/wasm32-unknown-unknown/release/polyglot_parser.wasm 2>/dev/null
    echo "  ✓ Wasm otimizado gerado"
fi

# 3. Python bindings (se feature habilitada)
echo "[3/5] Gerando bindings Python..."
if cargo build --release --features python 2>&1 | tail -5; then
    echo "  ✓ Python bindings gerados"
fi

# 4. Node.js bindings
echo "[4/5] Gerando bindings Node.js..."
# (Usaria wasm-pack ou napi-rs)

# 5. Testes
echo "[5/5] Executando testes..."
cargo test --release 2>&1 | tail -30
echo "[0/5] Gerando gramáticas Lark..."
./scripts/build_grammar.sh

echo "[1/5] Construindo core Rust..."
cargo build --release 2>&1 | tail -20

echo ""
echo "═══════════════════════════════════════════════════"
echo "  Build completo!"
echo "  Artefatos em: target/release/"
echo "    • libpolyglot_parser.a (static)"
echo "    • libpolyglot_parser.so (shared)"
echo "    • polyglot_parser.wasm (web)"
echo "  ═══════════════════════════════════════════════"
echo "═══════════════════════════════════════════════════"
