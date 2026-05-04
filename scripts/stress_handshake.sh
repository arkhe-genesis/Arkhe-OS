#!/bin/bash
# stress_handshake.sh
# Aplica latência e perda de pacotes simulando link de satélite e inicia o handshake.

LATENCY="600ms"
LOSS="5%"

echo "Aplicando condições de rede estressadas ($LATENCY, $LOSS)..."

# Tenta usar tc, mas ignora erro se não tiver permissão/ferramenta
if command -v tc >/dev/null 2>&1; then
    sudo tc qdisc add dev eth0 root netem delay $LATENCY loss $LOSS 2>/dev/null || \
    echo "⚠️ Falha ao aplicar tc (permissão?). Prosseguindo sem simulação de rede física."
else
    echo "⚠️ Comando 'tc' não encontrado."
fi

echo "Iniciando handshake..."
python3 scripts/global_handshake.py

# Limpeza
if command -v tc >/dev/null 2>&1; then
    sudo tc qdisc del dev eth0 root 2>/dev/null
fi

echo "✅ Stress test concluído."
