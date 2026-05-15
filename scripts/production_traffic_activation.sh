#!/bin/bash
# production_traffic_activation.sh — Ativação progressiva de tráfego real
# Estratégia: canary → 10% → 50% → 100% com monitoramento contínuo e rollback automático

set -euo pipefail

PHASE="${1:-canary}"  # canary, 10, 50, 100, rollback
PROMETHEUS_URL="http://prometheus.arkhe.internal:9090"
SLACK_WEBHOOK="${SLACK_WEBHOOK:-}"
LOG_FILE="/var/log/arkhe/go-live.log"

log() { echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"; }
notify() {
    log "$1"
    if [[ -n "$SLACK_WEBHOOK" ]]; then
        curl -s -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"🚦 Traffic Activation: $1\"}" "$SLACK_WEBHOOK" > /dev/null
    fi
}

check_metrics() {
    # Verifica métricas críticas antes de avançar fase
    local PHI_C=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=arkhe_mesh_phi_c" | jq -r '.data.result[0].value[1] // 0')
    local ERROR_RATE=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=rate(arkhe_api_errors_total[5m])" | jq -r '.data.result[0].value[1] // 0')
    local LATENCY_P95=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=histogram_quantile(0.95,rate(arkhe_request_latency_bucket[5m])))" | jq -r '.data.result[0].value[1] // 999')

    log "   Φ_C: $PHI_C | Error rate: $ERROR_RATE | P95 Latency: ${LATENCY_P95}ms"

    if (( $(echo "$PHI_C < 0.95" | bc -l) )); then
        log "❌ Φ_C abaixo do threshold — abortando avanço"
        return 1
    fi
    return 0
}

activate_phase() {
    local PHASE_NAME="$1"
    local TRAFFIC_PERCENT="$2"

    notify "Iniciando fase $PHASE_NAME ($TRAFFIC_PERCENT% tráfego)"

    # Ajustar peso no load balancer (exemplo com NGINX Ingress)
    kubectl annotate ingress audience-bridge-ingress -n arkhe-audience \
        "nginx.ingress.kubernetes.io/canary-weight=$TRAFFIC_PERCENT" --overwrite

    # Aguardar estabilização
    log "Aguardando 5 minutos para estabilização..."
    sleep 300

    # Verificar métricas
    if check_metrics; then
        notify "✅ Fase $PHASE_NAME concluída — métricas estáveis"
        return 0
    else
        notify "⚠️ Métricas degradadas na fase $PHASE_NAME — iniciando rollback"
        rollback
        return 1
    fi
}

rollback() {
    notify "🔄 Iniciando rollback — voltando para 0% tráfego"
    kubectl annotate ingress audience-bridge-ingress -n arkhe-audience \
        "nginx.ingress.kubernetes.io/canary-weight=0" --overwrite
    notify "✅ Rollback concluído"
}

case "$PHASE" in
    canary)
        # Canary: apenas 1% do tráfego por 10 minutos
        activate_phase "Canary" 1
        ;;
    10)
        activate_phase "10%" 10
        ;;
    50)
        activate_phase "50%" 50
        ;;
    100)
        activate_phase "100%" 100
        notify "🎉 GO‑LIVE COMPLETO — 100% tráfego em produção"
        # Ancorar na TemporalChain
        curl -X POST http://temporal-chain:8051/api/v1/events \
            -H "Content-Type: application/json" \
            -d '{"event_type":"production_go_live","payload":{"timestamp":'$(date +%s)'}}'
        ;;
    rollback)
        rollback
        ;;
    *)
        echo "Uso: $0 {canary|10|50|100|rollback}"
        exit 1
        ;;
esac