#!/bin/bash
# agictl federate — Comandos de gestão da federação

CMD=${1:-"status"}

case "$CMD" in
    join)
        SEED="${2:-arkhe-seed-01.onion}"
        echo "🌐 Juntando‑se à federação via $SEED..."
        podman exec arkhe-federate-pod-federate-daemon python3 -c "
from arkhe_federate import ArkheFederateDaemon
d = ArkheFederateDaemon()
d.config['bootstrap_nodes'] = ['$SEED']
d.run()
"
        ;;
    list-peers)
        echo "📡 Lista de peers conhecidos:"
        podman exec arkhe-federate-pod-federate-daemon python3 -c "
from arkhe_federate import ArkheFederateDaemon
d = ArkheFederateDaemon()
for p in d.dht.peers.values():
    print(f'{p.onion} (Φ={p.coherence:.2f})')
"
        ;;
    status)
        echo "📊 Status da Federação:"
        podman ps --pod --filter name=arkhe-federate-pod
        ;;
    *)
        echo "Uso: agictl federate {join|list-peers|status}"
        ;;
esac