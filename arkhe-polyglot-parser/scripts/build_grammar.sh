#!/bin/bash
# Compila todas as gramáticas Lark para Rust

set -e
GRAMMAR_DIR="parser-core/languages"
OUTPUT_DIR="parser-core/src/languages/generated"

mkdir -p "$OUTPUT_DIR"

# Avoid failing if directory is empty
shopt -s nullglob
for grammar in "$GRAMMAR_DIR"/*.lark; do
    name=$(basename "$grammar" .lark)
    echo "🔧 Compiling $name.lark → Rust..."
    python3 scripts/lark_to_rust.py \
        --grammar "$grammar" \
        --output "$OUTPUT_DIR/${name}_parser.rs" \
        --module "$name"
done

echo "✅ All grammars compiled to Rust"
