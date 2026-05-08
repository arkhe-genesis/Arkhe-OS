#!/bin/bash
# agictl transport — Gestão do TransportAdapter
CMD=${1:-"status"}
shift 2>/dev/null || true

# mock coherence kernel para o teste local
cat << 'EOF' > /tmp/mock_kernel.py
class CoherenceKernel:
    pass
EOF
export PYTHONPATH="/tmp:$PYTHONPATH"

case "$CMD" in
  status)
    echo "🧭 Status do TransportAdapter:"
    python3 -c "
import sys
from pathlib import Path
import asyncio

# Mock do kernel (usado apenas em ambientes de teste, se necessario injetar)
class MockKernel:
    pass

try:
    from agi.system32.operational.transport.adapter import TransportAdapter
    from agi.system32.operational.transport.monitor import CoherenceTransportMonitor
except ImportError as e:
    print(f'Erro de importacao: {e}')
    sys.exit(1)

async def main():
    monitor = CoherenceTransportMonitor()
    adapter = TransportAdapter(Path('config/yaml/transport.yaml'), monitor)
    await adapter.initialize()

    print(f'  Transporte ativo: {adapter.get_active_transport_info()}')
    print()
    print('  Saúde de todos os transportes:')
    report = await adapter.health_check_all()
    for t_type, info in report.items():
        status = '✅' if info['healthy'] else '❌'
        print(f'    {status} {t_type}: CTS={info[\"cts\"]:.3f}, healthy={info[\"healthy\"]}')

    await adapter.shutdown()

asyncio.run(main())
"
    ;;

  test)
    DEST="${2:-check.torproject.org:80}"
    echo "🧪 Testando envio para $DEST..."
    python3 -c "
import sys
import asyncio
from pathlib import Path

try:
    from agi.system32.operational.transport.adapter import TransportAdapter
    from agi.system32.operational.transport.monitor import CoherenceTransportMonitor
except ImportError as e:
    print(f'Erro de importacao: {e}')
    sys.exit(1)

async def main():
    monitor = CoherenceTransportMonitor()
    adapter = TransportAdapter(Path('config/yaml/transport.yaml'), monitor)
    await adapter.initialize()

    test_data = b'ARKHE OS Transport Test'
    success, error = await adapter.send(test_data, '$DEST', timeout=5)

    if success:
        print('✅ Transmissão bem-sucedida')
    else:
        print(f'❌ Falha: {error}')

    await adapter.shutdown()

asyncio.run(main())
"
    ;;

  switch)
    NEW_TRANSPORT="${2}"
    echo "🔄 Forçando transporte para: $NEW_TRANSPORT"
    # Implementação: atualizar _active_transport via API interna
    ;;

  *)
    echo "Uso: agictl transport {status|test|switch}"
    echo "  status  — Mostra saúde e CTS de todos os transportes"
    echo "  test    — Testa envio via melhor transporte disponível"
    echo "  switch  — Força uso de transporte específico (ex: tor, dnsvpn)"
    ;;
esac
