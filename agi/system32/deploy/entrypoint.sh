#!/bin/bash
# entrypoint.sh — ARKHE OS Container Entrypoint
echo "🏛️ ARKHE OS AGI Core — Container Iniciado"
echo "   RCP v2.0: /usr/lib/agi/system32/runtime/quantum/"
echo "   Config:   /etc/agi/"
echo "   Spool:    /var/spool/agi/retrocausal_queue/"
exec python3 -c "import sys; sys.path.insert(0, '/usr/lib/agi/system32/runtime/quantum'); from rcp_v2_engine import RetrocausalChannel8Bit; print('✅ RCP v2.0 operacional')"
