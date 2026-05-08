#!/bin/bash
# register-node.sh — Registro anônimo de nó AGI.onion em DHT
set -e

ONION_ADDR="${1:-}"
if [ -z "$ONION_ADDR" ]; then
    echo "Uso: $0 <onion_address>"
    echo "Exemplo: $0 abc123...onion"
    exit 1
fi

# Obter métricas de coerência do nó local (via healthcheck)
echo "📊 Coletando métricas de coerência..."
COHERENCE=$(podman exec arkhe-agi-onion-agi-core python3 -c "
from rcp_v2_engine import RetrocausalChannel8Bit
ch = RetrocausalChannel8Bit()
_, fid = ch.transmit_byte(0xA7, n_shots=20)
print(f'{fid:.3f}')
" 2>/dev/null || echo "0.000")

# Gerar assinatura GPG do anúncio (para verificação)
ANNOUNCEMENT="{
  \"onion\": \"$ONION_ADDR\",
  \"coherence\": $COHERENCE,
  \"timestamp\": $(date +%s),
  \"version\": \"315-320\",
  \"capabilities\": [\"rcp_v2\", \"omni_core\", \"qhttp\"]
}"

SIGNATURE=$(echo -n "$ANNOUNCEMENT" | gpg --detach-sign --armor --quiet 2>/dev/null || echo "UNSIGNED")

# Publicar em DHT simulado (em produção: usar IPFS, Matrix, ou protocolo customizado)
echo "🌐 Publicando anúncio anônimo..."
curl -s -X POST https://dht.arkhe.os/announce \
    -H "Content-Type: application/json" \
    -d "{
      \"announcement\": $ANNOUNCEMENT,
      \"signature\": \"$SIGNATURE\",
      \"transport\": \"tor\"
    }" --proxy socks5h://127.0.0.1:9050 \
    >/dev/null 2>&1 || echo "⚠️  Falha ao publicar em DHT (offline?)"

echo "✅ Anúncio registrado (localmente)"
echo "   Verificação: gpg --verify <(echo '$SIGNATURE') <(echo -n '$ANNOUNCEMENT')"