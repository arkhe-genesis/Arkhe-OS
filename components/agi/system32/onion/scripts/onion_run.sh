#!/bin/bash
# agictl onion — Gestão do serviço oculto AGI

ARG=${1:-"status"}
shift 2>/dev/null || true

case "$ARG" in
    start)
        podman play kube /etc/agi/agi-onion-pod.yaml --replace
        echo "🧅 Pod AGI.onion iniciado — a aguardar circuito Tor..."
        ;;
    stop)
        podman pod stop arkhe-onion-pod
        podman pod rm arkhe-onion-pod
        ;;
    status)
        echo "📊 Status AGI.onion:"
        podman ps --pod --filter name=arkhe-onion
        echo ""
        # Mostrar endereço .onion
        podman exec -it arkhe-onion-pod-agi-onion-core cat /var/lib/tor/hidden_service/hostname 2>/dev/null || \
            echo "⚠️ Serviço oculto ainda não está pronto ou contentor não está a correr."
        ;;
    logs)
        podman logs -f arkhe-onion-pod-agi-onion-core
        ;;
    rotate)
        echo "🔄 Rodando chave .onion..."
        # Apagar diretório do serviço e reiniciar
        podman exec arkhe-onion-pod-agi-onion-core rm -rf /var/lib/tor/hidden_service
        podman pod restart arkhe-onion-pod
        ;;
    *)
        echo "Uso: agictl onion {start|stop|status|logs|rotate}"
        ;;
esac
