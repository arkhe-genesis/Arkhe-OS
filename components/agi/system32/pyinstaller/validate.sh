#!/bin/bash
# validate.sh — Valida o binário ARKHE AGI após o build

set -e

BINARY="./dist/arkhe-agi"
MIN_COHERENCE=0.7

echo "🧪 Validando binário ARKHE AGI..."

# 1. Verificar se o binário existe e é executável
if [ ! -x "$BINARY" ]; then
    echo "❌ Binário não encontrado ou não executável"
    exit 1
fi

# 2. Testar comando de versão
echo "  Testando --version..."
$BINARY --version

# 3. Testar comando de status (modo offline/simulado)
echo "  Testando status..."
$BINARY status --offline

# 4. Testar coerência mínima
echo "  Testando coerência..."
COHERENCE=$($BINARY coherence --quick 2>/dev/null || echo "0.0")
echo "  Φ_C = $COHERENCE"

if awk -v c="$COHERENCE" -v min="$MIN_COHERENCE" 'BEGIN {exit !(c < min)}'; then
    echo "❌ Coerência abaixo do mínimo ($MIN_COHERENCE)"
    exit 1
fi

# 5. Testar geração de exemplo (inferência)
echo "  Testando geração..."
$BINARY generate --prompt "test" --max-tokens 10 --output /tmp/test_gen.json

# 6. Verificar checksum
if [ -f dist/arkhe-agi.sha256 ]; then
    echo "🔍 Verificando checksum..."
    sha256sum -c dist/arkhe-agi.sha256
fi

echo "✅ Validação concluída com sucesso!"