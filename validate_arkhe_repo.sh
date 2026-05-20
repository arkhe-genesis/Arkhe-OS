#!/bin/bash
# validate_arkhe_repo.sh — Validação da Regra dos 137 no Repositório Arkhe
# Canon: ∞.Ω.∇+++.319.validate_arkhe

set -e

echo "🏛️ ARKHE Ω‑TEMP v∞.Ω — Substrate 319: Validate Arkhe Repository"
echo "   Canon: ∞.Ω.∇+++.319.validate_arkhe"
echo "   Alpha⁻¹: 137.035999084"
echo ""

# Configurações
ARKHE_ROOT="${ARKHE_HOME:-.}"
REPORT_DIR="${ARKHE_ROOT}/var/evidence"
TIMESTAMP=$(date -u +"%Y%m%dT%H%M%SZ")
REPORT_FILE="${REPORT_DIR}/alpha_validation_${TIMESTAMP}.json"

# Criar diretório de evidências se não existir
mkdir -p "${REPORT_DIR}"

# Executar check_137_rule.py com output JSON
echo "🔍 Executando check_137_rule.py no repositório Arkhe..."
python3 check_137_rule.py "${ARKHE_ROOT}" --json --limit 137 > "${REPORT_FILE}" 2>&1 || true

# Analisar resultados
COMPLIANT=$(python3 -c "import json; r=json.load(open('${REPORT_FILE}')); print('true' if r['compliant'] else 'false')")

if [ "$COMPLIANT" = "true" ]; then
    echo "✅ Repositório Arkhe RESPEITA a Regra dos 137"
    echo "   Relatório: ${REPORT_FILE}"

    # Ancorar na TemporalChain
    SEAL=$(python3 -c "
import json, hashlib
r = json.load(open('${REPORT_FILE}'))
payload = {**r, 'event': 'arkhe_repo_validated', 'timestamp': '${TIMESTAMP}'}
print(hashlib.sha3_256(json.dumps(payload, sort_keys=True).encode()).hexdigest())
")
    echo "   Selo TemporalChain: ${SEAL[:32]}..."

    exit 0
else
    echo "⚠️  Repositório Arkhe VIOLA a Regra dos 137"
    echo "   Relatório: ${REPORT_FILE}"

    VIOLATIONS=$(python3 -c "import json; r=json.load(open('${REPORT_FILE}')); print(len(r['violations']))")
    echo "   Violações: ${VIOLATIONS}"

    # Listar diretórios problemáticos
    echo ""
    echo "📋 Diretórios que violam α⁻¹:"
    python3 -c "
import json
r = json.load(open('${REPORT_FILE}'))
for v in r['violations']:
    print(f\"   • {v['path']}: {v['count']} itens (limite: {v['limit']})\")
"

    # Sugerir auto-fission
    echo ""
    echo "💡 Para corrigir automaticamente:"
    echo "   python auto_fission.py ${REPORT_FILE} --dry-run  # Simular primeiro"
    echo "   python auto_fission.py ${REPORT_FILE}            # Executar com confirmação"

    exit 1
fi
