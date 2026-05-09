#!/bin/sh
# entrypoint.sh — ARKHE OS AGI Core Container Entrypoint
set -e

echo "🏛️ ARKHE OS AGI Core — Podman Container Iniciado"
echo "   User: $(whoami)"
echo "   Runtime: $(python3 --version)"

# Verificar se a ponte FFI existe
if [ -f /home/agi/system32/agi_rcp_bridge.so ]; then
    echo "✅ Ponte FFI carregada"
else
    echo "⚠️  Ponte FFI ausente — funcionalidades retrocausais indisponíveis"
fi

# Iniciar motor RCP e Omni
exec python3 -c "
from rcp_v2_engine import RetrocausalChannel8Bit
from omni_core import OmniCore
import os, time

channel = RetrocausalChannel8Bit()
print(f'✅ RCP v2.0 operacional — Fidelidade base: {channel.transmit_byte(0xA7)[1]:.1%}')

core = OmniCore()
core.initialize(phi_seed=0.72)
print(f'✅ Omni Core ativo — κ inicial: {core.calibration.kappa:.3f}')

# Loop principal
while True:
    try:
        result = core.cycle(phi_local=0.72, steps=1)
        print(f'[{os.getpid()}] Φ_C: {result[\"final_phi\"]:.3f} | Confiança: {result[\"final_confidence\"]:.1%}')
        time.sleep(1)
    except KeyboardInterrupt:
        break
"
