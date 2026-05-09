#!/bin/bash
# agictl transport — Gestão do TransportAdapter
CMD=${1:-"status"}
shift 2>/dev/null || true

case "$CMD" in
  status)
    echo "🧭 Status do TransportAdapter:"
    python3 -c "
from agi.system32.operational.transport.adapter import TransportAdapter
import asyncio
from pathlib import Path

class MockCoherenceMonitor:
    def evaluate_transmission_coherence(self, data): return 0.9

async def main():
    adapter = TransportAdapter(Path('agi/system32/operational/transport/config/transport.yaml'), MockCoherenceMonitor())
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
import asyncio
from pathlib import Path
from agi.system32.operational.transport.adapter import TransportAdapter

class MockCoherenceMonitor:
    def evaluate_transmission_coherence(self, data): return 0.9

async def main():
    adapter = TransportAdapter(Path('agi/system32/operational/transport/config/transport.yaml'), MockCoherenceMonitor())
    await adapter.initialize()

    test_data = b'ARKHE OS Transport Test'
    success, error = await adapter.send(test_data, '$DEST', timeout=30)

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
    echo "  switch  — Força uso de transporte específico (ex: tor, masterdnsvpn)"
    ;;
esac