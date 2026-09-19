#!/usr/bin/env bash
set -euo pipefail

echo '=== pacir-q: verificação completa ==='
cargo build --workspace --all-targets
cargo test --workspace --quiet
if command -v cargo-kani &>/dev/null; then cargo kani -p pacir-q-kani --quiet; else echo 'Kani não instalado — pulando'; fi
cargo run -q -p pacir-q-cli -- alpha
cargo run -q -p pacir-q-cli -- report
