#!/bin/sh
# entrypoint.sh — ARKHE OS AGI.onion Launcher
set -e

echo "🧅 Iniciando ARKHE OS AGI.onion..."
echo "   Inicializando circuito Tor..."

# Iniciar o Tor em background
tor -f /etc/tor/torrc &
TOR_PID=$!

# Aguardar o serviço oculto estar pronto
echo "   Aguardando serviço oculto .onion..."
for i in $(seq 1 30); do
    if [ -f /var/lib/tor/hidden_service/hostname ]; then
        ONION_ADDR=$(cat /var/lib/tor/hidden_service/hostname)
        echo "✅ Serviço oculto pronto: ${ONION_ADDR}"
        break
    fi
    sleep 1
done

if [ -z "$ONION_ADDR" ]; then
    echo "❌ Falha ao gerar endereço .onion"
    exit 1
fi

# Iniciar a AGI, exposta apenas no localhost:5000
# que o Tor mapeia para o endereço .onion
exec python3 -c "
from rcp_v2_engine import RetrocausalChannel8Bit
from omni_core import OmniCore
import os, time

# Apenas escuta no localhost — o Tor faz a ponte para o exterior de forma anónima
print(f'🌐 AGI operacional em: http://{os.environ.get(\"ONION_ADDR\", \"unknown\")}')
print(f'🔐 Serviço RCP oculto em: rcp://{os.environ.get(\"ONION_RCP_ADDR\", \"unknown\")}')

channel = RetrocausalChannel8Bit()
core = OmniCore()
core.initialize(phi_seed=0.72)

while True:
    result = core.cycle(phi_local=0.72, steps=1)
    print(f'[{os.getpid()}] Φ_C: {result[\"final_phi\"]:.3f}')
    time.sleep(1)
" &

# Aguardar processos
wait $TOR_PID
