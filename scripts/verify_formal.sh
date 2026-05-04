#!/usr/bin/env bash
# scripts/verify_formal.sh — Executar provas de segurança com Kani
set -euo pipefail

echo "🔐 ARKHE OS v168.1 — Verificação Formal com Kani"

# Verificar instalação do Kani
if ! command -v kani &> /dev/null; then
    echo "❌ Kani não encontrado. Instalando..."
    cargo install --locked kani-verifier
    kani setup
fi

# Executar provas
echo "🧪 Executando provas de safety..."
./build/kani/run_proofs.sh

echo ""
echo "✅ Verificação formal concluída!"
