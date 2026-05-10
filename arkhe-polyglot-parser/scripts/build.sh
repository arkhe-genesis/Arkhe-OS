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

echo "[1/5] Construindo core Rust..."
cargo build --release 2>&1 | tail -20

echo ""
echo "═══════════════════════════════════════════════════"
echo "  Build completo!"
echo "  Artefatos em: target/release/"
echo "═══════════════════════════════════════════════════"
