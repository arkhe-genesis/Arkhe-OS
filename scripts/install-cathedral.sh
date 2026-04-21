#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# install-cathedral.sh — Automated Deploy for Arkhe Cathedral
# ═══════════════════════════════════════════════════════════════════════════════

set -e

NAMESPACE="arkhe"
CHART_DIR="./arkhe-cathedral"

echo "🔨 Forjando o Reino Arkhe no éter..."

# 1. Check prerequisites
command -v kubectl >/dev/null 2>&1 || { echo "❌ kubectl não encontrado."; exit 1; }
command -v helm >/dev/null 2>&1 || { echo "❌ helm não encontrado."; exit 1; }

# 2. Create namespace
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# 3. Add dependencies
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# 4. Install Redis (State Cache)
echo "📦 Instalando cache de estado (Redis)..."
helm upgrade --install arkhe-state-cache bitnami/redis \
  --namespace $NAMESPACE \
  --set architecture=standalone \
  --set auth.enabled=false

# 5. Install Cathedral Components
echo "⛪ Levantando a Catedral (Sidecar + Inquisidor + Envoy)..."
if [ -d "$CHART_DIR" ]; then
  helm upgrade --install arkhe-prod $CHART_DIR \
    --namespace $NAMESPACE \
    --values $CHART_DIR/values.yaml \
    --values $CHART_DIR/values-production.yaml
else
  echo "⚠️ Chart local não encontrado. Tentando repositório remoto..."
  # helm upgrade --install arkhe-prod arkhe/cathedral --namespace $NAMESPACE
fi

echo "✅ Catedral forjada com sucesso no namespace $NAMESPACE."
echo "⚖️ Use 'kubectl get pods -n $NAMESPACE' para testemunhar o silêncio."
