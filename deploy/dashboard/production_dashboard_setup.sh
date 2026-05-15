#!/bin/bash
# deploy/dashboard/production_dashboard_setup.sh
# Deploy do dashboard Streamlit em produção com alertas Prometheus ativos

set -euo pipefail

DASHBOARD_IMAGE="${DASHBOARD_IMAGE:-arkhe/singularity-dashboard:1.0.0}"
DASHBOARD_PORT="${DASHBOARD_PORT:-8501}"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://prometheus.arkhe.internal:9090}"
ALERTMANAGER_URL="${ALERTMANAGER_URL:-http://alertmanager.arkhe.internal:9093}"
VAULT_ADDR="${VAULT_ADDR:-https://vault.arkhe.internal:8200}"

log_info() { echo -e "\033[0;32m[INFO]\033[0m $1"; }
log_error() { echo -e "\033[0;31m[ERROR]\033[0m $1"; exit 1; }

# ============================================================================
# CONFIGURAR ALERTAS PROMETHEUS
# ============================================================================

deploy_alert_rules() {
    log_info "Configurando regras de alerta Prometheus..."

    cat > /tmp/arkhe-alerts.yaml << 'ALERTS'
groups:
- name: arkhe_singularity_alerts
  rules:

  # Alerta: Φ_C abaixo do threshold crítico
  - alert: PhiCCriticalLow
    expr: arkhe_singularity_global_phi_c < 0.90
    for: 2m
    labels:
      severity: critical
      team: singularity-ops
    annotations:
      summary: "Φ_C crítico baixo — coerência da malha comprometida"
      description: "Φ_C global = {{ $value }} (< 0.90) por mais de 2 minutos"
      runbook: "https://wiki.arkhe.internal/runbooks/phi-c-critical"

  # Alerta: Φ_C abaixo do threshold de warning
  - alert: PhiCWarningLow
    expr: arkhe_singularity_global_phi_c < 0.95
    for: 5m
    labels:
      severity: warning
      team: singularity-ops
    annotations:
      summary: "Φ_C abaixo do target"
      description: "Φ_C global = {{ $value }} (< 0.95) por mais de 5 minutos"

  # Alerta: Perda de nós ativos
  - alert: NodesDropped
    expr: changes(arkhe_singularity_nodes_total{status="active"}[5m]) < -5
    for: 1m
    labels:
      severity: warning
    annotations:
      summary: "Queda abrupta de nós ativos"
      description: "{{ $value }} nós perdidos em 5 minutos"

  # Alerta: Latência de processamento alta
  - alert: ProcessingLatencyHigh
    expr: histogram_quantile(0.99, rate(arkhe_spark_processing_latency_seconds_bucket[5m])) > 0.5
    for: 3m
    labels:
      severity: warning
    annotations:
      summary: "Latência de processamento acima do threshold"
      description: "P99 latency = {{ $value }}s (> 500ms)"

  # Alerta: Kafka consumer lag alto
  - alert: KafkaConsumerLagCritical
    expr: kafka_consumer_lag{topic="chat_messages"} > 100000
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "Consumer lag crítico no Kafka"
      description: "Lag = {{ $value }} mensagens — risco de perda de dados"

  # Alerta: Falha de assinatura PQC
  - alert: PQCSigningFailures
    expr: rate(arkhe_pqc_signing_errors_total[5m]) > 0
    for: 1m
    labels:
      severity: critical
      team: security
    annotations:
      summary: "Falhas em assinaturas PQC detectadas"
      description: "{{ $value }} erros/s em assinaturas PQC"

  # Alerta: Dashboard indisponível
  - alert: DashboardDown
    expr: up{job="singularity-dashboard"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Dashboard de monitoramento indisponível"
      description: "O dashboard Streamlit não está respondendo"

- name: arkhe_audience_bridge_alerts
  rules:

  # Alerta: Audiência anômala (possível view-botting)
  - alert: AudienceAnomalyDetected
    expr: |
      abs(delta(arkhe_audience_total_viewers[5m])) /
      arkhe_audience_total_viewers > 0.5
    for: 2m
    labels:
      severity: warning
      team: data-integrity
    annotations:
      summary: "Variação anômala na contagem de audiência"
      description: "Mudança de {{ $value | humanizePercentage }} em 5 minutos"

  # Alerta: Φ_C de dados de audiência baixo
  - alert: AudienceDataPhiCLow
    expr: arkhe_audience_phi_c_coherence < 0.95
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Qualidade dos dados de audiência comprometida"
      description: "Φ_C dos dados = {{ $value }} (< 0.95)"
ALERTS

    # Aplicar regras no Prometheus via API
    curl -X POST -H "Content-Type: application/yaml" \
        --data-binary @/tmp/arkhe-alerts.yaml \
        "${PROMETHEUS_URL}/api/v1/rules"

    log_info "✅ Regras de alerta aplicadas"
}

# ============================================================================
# CONFIGURAR ALERTMANAGER
# ============================================================================

configure_alertmanager() {
    log_info "Configurando rotas de notificação no Alertmanager..."

    cat > /tmp/alertmanager-config.yaml << 'AMCONFIG'
global:
  resolve_timeout: 5m
  smtp_smarthost: 'smtp.arkhe.internal:587'
  smtp_from: 'alerts@arkhe.internal'

route:
  group_by: ['alertname', 'severity', 'team']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'default-receiver'
  routes:
  - match:
      severity: critical
    receiver: 'critical-pagerduty'
    continue: true
  - match:
      team: security
    receiver: 'security-slack'
  - match:
      team: singularity-ops
    receiver: 'ops-slack'

receivers:
- name: 'default-receiver'
  email_configs:
  - to: 'ops-team@arkhe.internal'
    send_resolved: true

- name: 'critical-pagerduty'
  pagerduty_configs:
  - service_key: '${PAGERDUTY_SERVICE_KEY}'
    severity: '{{ .CommonLabels.severity }}'
    description: '{{ .CommonAnnotations.summary }}'

- name: 'security-slack'
  slack_configs:
  - api_url: '${SLACK_SECURITY_WEBHOOK}'
    channel: '#security-alerts'
    title: '🔐 Alerta de Segurança ARKHE'
    text: '{{ range .Alerts }}*{{ .Annotations.summary }}*\n{{ .Annotations.description }}\n{{ end }}'

- name: 'ops-slack'
  slack_configs:
  - api_url: '${SLACK_OPS_WEBHOOK}'
    channel: '#singularity-ops'
    title: '⚛️ Alerta Operacional ARKHE'
    text: '{{ range .Alerts }}*{{ .Annotations.summary }}*\n{{ .Annotations.description }}\n{{ end }}'

inhibit_rules:
- source_match:
    severity: 'critical'
  target_match:
    severity: 'warning'
  equal: ['alertname', 'instance']
AMCONFIG

    # Validar configuração
    amtool check-config /tmp/alertmanager-config.yaml

    # Recarregar Alertmanager
    curl -X POST "${ALERTMANAGER_URL}/-/reload"

    log_info "✅ Configuração do Alertmanager aplicada"
}

# ============================================================================
# DEPLOY DO DASHBOARD STREAMLIT
# ============================================================================

deploy_dashboard() {
    log_info "Fazendo deploy do dashboard Streamlit..."

    # Criar namespace se não existir
    kubectl create namespace arkhe-dashboard --dry-run=client -o yaml | kubectl apply -f -

    # Deploy via Kubernetes
    cat << EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: singularity-dashboard
  namespace: arkhe-dashboard
spec:
  replicas: 2
  selector:
    matchLabels:
      app: singularity-dashboard
  template:
    metadata:
      labels:
        app: singularity-dashboard
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8501"
    spec:
      serviceAccountName: arkhe-dashboard-sa
      containers:
      - name: dashboard
        image: ${DASHBOARD_IMAGE}
        ports:
        - containerPort: 8501
          name: http
        env:
        - name: PROMETHEUS_URL
          value: "${PROMETHEUS_URL}"
        - name: ALERTMANAGER_URL
          value: "${ALERTMANAGER_URL}"
        - name: VAULT_ADDR
          value: "${VAULT_ADDR}"
        - name: STREAMLIT_SERVER_PORT
          value: "8501"
        - name: STREAMLIT_SERVER_ADDRESS
          value: "0.0.0.0"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8501
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8501
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: singularity-dashboard
  namespace: arkhe-dashboard
spec:
  selector:
    app: singularity-dashboard
  ports:
  - port: 80
    targetPort: 8501
    protocol: TCP
    name: http
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: dashboard-ingress
  namespace: arkhe-dashboard
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/auth-type: "basic"
    nginx.ingress.kubernetes.io/auth-secret: "dashboard-basic-auth"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - dashboard.arkhe.internal
    secretName: dashboard-tls
  rules:
  - host: dashboard.arkhe.internal
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: singularity-dashboard
            port:
              name: http
EOF

    # Aguardar deploy ficar ready
    kubectl rollout status deployment/singularity-dashboard -n arkhe-dashboard --timeout=120s

    log_info "✅ Dashboard deployado: https://dashboard.arkhe.internal"
}

# ============================================================================
# VALIDAR DEPLOY
# ============================================================================

validate_dashboard() {
    log_info "Validando deploy do dashboard..."

    # Verificar pods
    if ! kubectl get pods -n arkhe-dashboard -l app=singularity-dashboard | grep -q "Running"; then
        log_error "Pods do dashboard não estão em execução"
    fi

    # Testar endpoint de health
    DASHBOARD_URL=$(kubectl get ingress -n arkhe-dashboard dashboard-ingress -o jsonpath='{.spec.rules[0].host}')
    if ! curl -sf "https://${DASHBOARD_URL}/health" &>/dev/null; then
        log_error "Endpoint de health do dashboard não responde"
    fi

    # Verificar métricas Prometheus
    if ! curl -sf "${PROMETHEUS_URL}/api/v1/query?query=arkhe_singularity_global_phi_c" | grep -q '"status":"success"'; then
        log_warn "Métricas de singularidade não encontradas no Prometheus"
    fi

    log_info "✅ Validação do dashboard concluída"
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    log_info "🚀 Iniciando deploy do dashboard em produção..."

    deploy_alert_rules
    configure_alertmanager
    deploy_dashboard
    validate_dashboard

    log_info "🎉 Deploy do dashboard concluído com sucesso!"
    log_info "   • URL: https://dashboard.arkhe.internal"
    log_info "   • Alertas: ${PROMETHEUS_URL}/alerts"
    log_info "   • Métricas: ${PROMETHEUS_URL}/graph"
    log_info ""
    log_info "🔔 Notificações configuradas:"
    log_info "   • Crítico: PagerDuty + Slack #security-alerts"
    log_info "   • Warning: Slack #singularity-ops"
    log_info "   • Info: Email ops-team@arkhe.internal"
}

main "$@"
