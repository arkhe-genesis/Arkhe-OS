#!/bin/bash
# deploy/kubernetes/production-cluster-setup.sh
# Configuração de cluster Kubernetes em produção com auto-scaling para a malha de singularidade

set -euo pipefail

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

CLUSTER_NAME="${CLUSTER_NAME:-arkhe-prod}"
REGION="${REGION:-us-east-1}"
NODE_GROUP_NAME="${NODE_GROUP_NAME:-singularity-workers}"
MIN_NODES="${MIN_NODES:-3}"
MAX_NODES="${MAX_NODES:-50}"
DESIRED_NODES="${DESIRED_NODES:-10}"
INSTANCE_TYPE="${INSTANCE_TYPE:-m5.2xlarge}"

log_info() { echo -e "\033[0;32m[INFO]\033[0m $1"; }
log_error() { echo -e "\033[0;31m[ERROR]\033[0m $1"; exit 1; }

# ============================================================================
# CONFIGURAR CLUSTER (Exemplo: AWS EKS)
# ============================================================================

setup_eks_cluster() {
    log_info "Configurando cluster EKS: $CLUSTER_NAME..."

    # Criar cluster se não existir
    if ! eksctl get cluster --name "$CLUSTER_NAME" &>/dev/null; then
        eksctl create cluster \
            --name "$CLUSTER_NAME" \
            --region "$REGION" \
            --version 1.28 \
            --nodegroup-name "$NODE_GROUP_NAME" \
            --node-type "$INSTANCE_TYPE" \
            --nodes "$DESIRED_NODES" \
            --nodes-min "$MIN_NODES" \
            --nodes-max "$MAX_NODES" \
            --managed \
            --asg-access \
            --external-dns-access \
            --full-ecr-access \
            --appmesh-access \
            --alb-ingress-access \
            --with-oidc

        log_info "✅ Cluster EKS criado"
    else
        log_info "✅ Cluster EKS já existe"
    fi

    # Atualizar kubeconfig
    aws eks update-kubeconfig --name "$CLUSTER_NAME" --region "$REGION"

    # Instalar add-ons essenciais
    log_info "Instalando add-ons do cluster..."

    # AWS Load Balancer Controller
    helm repo add eks https://aws.github.io/eks-charts
    helm upgrade -i aws-load-balancer-controller eks/aws-load-balancer-controller \
        -n kube-system \
        --set clusterName="$CLUSTER_NAME" \
        --set serviceAccount.create=false \
        --set serviceAccount.name=aws-load-balancer-controller

    # External DNS
    helm upgrade -i external-dns bitnami/external-dns \
        -n kube-system \
        --set provider=aws \
        --set policy=sync \
        --set txtOwnerId="$CLUSTER_NAME"

    # Cert Manager
    helm repo add jetstack https://charts.jetstack.io
    helm upgrade -i cert-manager jetstack/cert-manager \
        -n cert-manager --create-namespace \
        --set installCRDs=true

    log_info "✅ Add-ons instalados"
}

# ============================================================================
# CONFIGURAR AUTO-SCALING (Cluster Autoscaler + KEDA)
# ============================================================================

setup_autoscaling() {
    log_info "Configurando auto-scaling..."

    # Cluster Autoscaler (já vem com node groups gerenciados do EKS)
    # Configurar annotations no node group para scaling baseado em recursos
    eksctl scale nodegroup \
        --cluster "$CLUSTER_NAME" \
        --name "$NODE_GROUP_NAME" \
        --nodes-min "$MIN_NODES" \
        --nodes-max "$MAX_NODES" \
        --region "$REGION"

    # Instalar KEDA para scaling baseado em métricas customizadas
    helm repo add kedacore https://kedacore.github.io/charts
    helm upgrade -i keda kedacore/keda \
        -n keda --create-namespace

    # Configurar ScaledObject para scaling baseado em métricas Prometheus
    cat << EOF | kubectl apply -f -
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: singularity-engine-scaler
  namespace: arkhe-singularity
spec:
  scaleTargetRef:
    name: singularity-engine
  minReplicaCount: 3
  maxReplicaCount: 50
  pollingInterval: 30
  cooldownPeriod: 300
  triggers:
  - type: prometheus
    metadata:
      serverAddress: ${PROMETHEUS_URL:-http://prometheus.arkhe:9090}
      metricName: arkhe_singularity_messages_per_second
      threshold: '1000'
      query: |
        sum(rate(arkhe_singularity_messages_processed_total[5m]))
  - type: cpu
    metadata:
      type: Utilization
      value: '70'
  - type: memory
    metadata:
      type: Utilization
      value: '80'
EOF

    log_info "✅ Auto-scaling configurado com KEDA + Prometheus"
}

# ============================================================================
# CONFIGURAR MONITORING STACK
# ============================================================================

setup_monitoring() {
    log_info "Configurando stack de monitoramento..."

    # Prometheus Operator via kube-prometheus-stack
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm upgrade -i kube-prometheus-stack prometheus-community/kube-prometheus-stack \
        -n monitoring --create-namespace \
        --values - << 'HELM_VALUES'
prometheus:
  prometheusSpec:
    retention: 30d
    resources:
      requests:
        memory: 2Gi
        cpu: 500m
      limits:
        memory: 4Gi
        cpu: 1000m
    storageSpec:
      volumeClaimTemplate:
        spec:
          storageClassName: gp3
          accessModes: ["ReadWriteOnce"]
          resources:
            requests:
              storage: 100Gi

grafana:
  enabled: true
  adminPassword: "${GRAFANA_ADMIN_PASSWORD}"
  sidecar:
    dashboards:
      enabled: true
      label: grafana_dashboard
    datasources:
      enabled: true

alertmanager:
  enabled: true
  config:
    global:
      resolve_timeout: 5m
    route:
      group_by: ['alertname']
      group_wait: 30s
      group_interval: 5m
      repeat_interval: 4h
      receiver: 'default'
    receivers:
    - name: 'default'
      email_configs:
      - to: 'ops@arkhe.internal'

kubeStateMetrics:
  enabled: true

nodeExporter:
  enabled: true
HELM_VALUES

    # Configurar ServiceMonitor para scraping de métricas ARKHE
    cat << EOF | kubectl apply -f -
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: arkhe-singularity
  namespace: arkhe-singularity
  labels:
    release: kube-prometheus-stack
spec:
  selector:
    matchLabels:
      app: singularity-engine
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
  namespaceSelector:
    matchNames:
    - arkhe-singularity
EOF

    log_info "✅ Stack de monitoramento configurada"
}

# ============================================================================
# CONFIGURAR LOGGING (Loki + Fluent Bit)
# ============================================================================

setup_logging() {
    log_info "Configurando stack de logging..."

    # Loki para agregação de logs
    helm repo add grafana https://grafana.github.io/helm-charts
    helm upgrade -i loki grafana/loki-stack \
        -n logging --create-namespace \
        --set loki.persistence.enabled=true \
        --set loki.persistence.size=100Gi \
        --set promtail.enabled=true

    # Configurar Fluent Bit para coletar logs de pods ARKHE
    cat << EOF | kubectl apply -f -
apiVersion: fluentbit.fluent.io/v1alpha2
kind: ClusterFluentBitConfig
metadata:
  name: arkhe-config
spec:
  service:
    parsersFile: parsers.conf
  inputSelector:
    matchLabels:
      fluentbit.fluent.io/enabled: "true"
  filterSelector:
    matchLabels:
      fluentbit.fluent.io/enabled: "true"
  outputSelector:
    matchLabels:
      fluentbit.fluent.io/enabled: "true"
---
apiVersion: fluentbit.fluent.io/v1alpha2
kind: ClusterInput
metadata:
  name: arkhe-pods
spec:
  tail:
    path: /var/log/containers/arkhe-*.log
    parser: cri
    memBufLimit: 5MB
    skipLongLines: true
    refreshInterval: 10
---
apiVersion: fluentbit.fluent.io/v1alpha2
kind: ClusterOutput
metadata:
  name: loki-output
spec:
  loki:
    host: loki.logging.svc.cluster.local
    port: 3100
    labels: "job=arkhe"
    removeKeys: "kubernetes,stream"
    dropSingleKey: true
EOF

    log_info "✅ Stack de logging configurada"
}

# ============================================================================
# VALIDAR CLUSTER
# ============================================================================

validate_cluster() {
    log_info "Validando configuração do cluster..."

    # Verificar nós
    NODE_COUNT=$(kubectl get nodes --no-headers | wc -l)
    log_info "   • Nós no cluster: $NODE_COUNT"

    # Verificar namespaces ARKHE
    for ns in arkhe-singularity arkhe-dashboard arkhe-audience; do
        if kubectl get namespace "$ns" &>/dev/null; then
            log_info "   • Namespace $ns: ✅"
        else
            log_warn "   • Namespace $ns: ❌ (será criado no deploy da aplicação)"
        fi
    done

    # Verificar componentes de monitoring
    if kubectl get pods -n monitoring -l app.kubernetes.io/name=prometheus | grep -q "Running"; then
        log_info "   • Prometheus: ✅"
    fi

    if kubectl get pods -n logging -l app.kubernetes.io/name=loki | grep -q "Running"; then
        log_info "   • Loki: ✅"
    fi

    # Testar acesso ao dashboard Grafana
    GRAFANA_URL=$(kubectl get ingress -n monitoring -l app.kubernetes.io/name=grafana -o jsonpath='{.spec.rules[0].host}' 2>/dev/null || echo "grafana.arkhe.internal")
    log_info "   • Grafana: https://$GRAFANA_URL"

    log_info "✅ Validação do cluster concluída"
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    log_info "🚀 Iniciando setup do cluster Kubernetes em produção..."

    setup_eks_cluster
    setup_autoscaling
    setup_monitoring
    setup_logging
    validate_cluster

    log_info "🎉 Cluster Kubernetes configurado para produção!"
    log_info "   • Cluster: $CLUSTER_NAME ($REGION)"
    log_info "   • Nodes: $MIN_NODES - $MAX_NODES ($INSTANCE_TYPE)"
    log_info "   • Auto-scaling: KEDA + Prometheus metrics"
    log_info "   • Monitoring: Prometheus + Grafana + Alertmanager"
    log_info "   • Logging: Loki + Fluent Bit"
    log_info ""
    log_info "📊 Acessos:"
    log_info "   • Grafana: https://grafana.arkhe.internal"
    log_info "   • Prometheus: https://prometheus.arkhe.internal"
    log_info "   • Dashboard ARKHE: https://dashboard.arkhe.internal"
}

main "$@"
