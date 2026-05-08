#!/bin/sh
# healthcheck.sh — Podman Healthcheck (verificação de coerência)
# Retorna 0 se saudável, 1 se não

# Tentar importar o motor RCP e verificar coerência
python3 -c "
try:
    from rcp_v2_engine import RetrocausalChannel8Bit
    ch = RetrocausalChannel8Bit()
    _, fidelity = ch.transmit_byte(0xA7, n_shots=10)
    if fidelity >= 0.6:
        print(f'HEALTHY: fidelity={fidelity:.2%}')
        exit(0)
    else:
        print(f'DEGRADED: fidelity={fidelity:.2%}')
        exit(1)
except Exception as e:
    print(f'CRITICAL: {e}')
    exit(1)
" 2>/dev/null

exit $?
