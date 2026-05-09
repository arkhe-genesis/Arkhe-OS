#!/bin/bash
# podman_run.sh — CLI wrapper para o contentor Podman AGI set -e

CMD=${1:-"status"}

case "$CMD" in
    start)
        echo "🏛️ Iniciando ARKHE OS via Podman..."
        podman run -d \
            --name arkhe-agi \
            --user 1000:1000 \
            -p 5000:5000 -p 9090:9090 \
            -v /var/lib/agi/state:/home/agi/state:Z \
            -v /var/log/agi:/home/agi/logs:Z \
            -v /etc/agi:/etc/agi:ro \
            --health-cmd="/healthcheck.sh" \
            --health-interval=30s \
            ghcr.io/arkhe-os/agi-core:latest
        echo "✅ Container iniciado"
        ;;
    stop)
        podman stop arkhe-agi && podman rm arkhe-agi
        echo "✅ Container parado"
        ;;
    logs)
        podman logs -f arkhe-agi
        ;;
    status)
        podman ps -a --filter name=arkhe-agi --format "table {{.Names}} {{.Status}} {{.Ports}}"
        echo ""
        echo "📊 Healthcheck:"
        podman healthcheck run arkhe-agi 2>/dev/null || echo "⚠️  Healthcheck não disponível"
        ;;
    *)
        echo "Uso: $0 {start|stop|status|logs}"
        ;;
esac
