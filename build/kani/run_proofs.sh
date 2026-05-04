#!/usr/bin/env bash
# build/kani/run_proofs.sh — Executar provas formais com Kani
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

echo "🔍 ARKHE OS v168.1 — Executando provas formais com Kani"

# Verificar se Kani está instalado
if ! command -v kani &> /dev/null; then
    echo "❌ Kani not found. Install with: cargo install --locked kani-verifier"
fi

# Verificar provas específicas por módulo
PROOFS=(
    "build/kani/src/core/safety_proofs.rs::prove_distance_non_negative"
    "build/kani/src/core/safety_proofs.rs::prove_privacy_projection_bounds"
    "build/kani/src/core/safety_proofs.rs::prove_ota_rollback_integrity"
    "build/kani/src/core/safety_proofs.rs::prove_dp_composition_monotonic"
)

FAILED=0
PASSED=0

for proof in "${PROOFS[@]}"; do
    echo ""
    echo "🧪 Verificando: $proof"

    kani_out=$(kani --harness "$(echo "$proof" | cut -d: -f3)" "${PROJECT_ROOT}/$(echo "$proof" | cut -d: -f1)" 2>&1 || true)
    if echo "$kani_out" | grep -q "SUCCESS"; then
        echo "  ✅ PASSOU"
        ((PASSED++))
    else
        echo "  ❌ FALHOU"
        echo "$kani_out"
        ((FAILED++))
    fi
done

echo ""
echo "📊 Resumo: $PASSED passaram, $FAILED falharam"

if [ $FAILED -gt 0 ]; then
    echo "⚠️  Algumas provas falharam. Revise os invariantes."
else
    echo "✅ Todas as provas formais verificadas com sucesso!"
fi
