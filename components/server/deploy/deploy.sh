#!/bin/bash
# tzinor/deploy/deploy.sh
set -e

echo "╔═══════════════════════════════════════════════════════════════════════════╗"
echo "║  ARKHE(N) CLUSTER DEPLOYMENT                                                ║"
echo "║  Protocol: qhttp:// + Hashtree P2P                                          ║"
echo "╚═══════════════════════════════════════════════════════════════════════════╝"

# Verificar dependências
command -v kubectl >/dev/null 2>&1 || { echo "kubectl required"; exit 1; }
command -v helm >/dev/null 2>&1 || { echo "helm required"; exit 1; }
command -v htree >/dev/null 2>&1 || { echo "hashtree CLI required"; exit 1; }

# 1. Criar namespace
echo "▶ Creating namespace..."
kubectl apply -f kubernetes/namespace.yaml

# 2. Configurar nodepool CUDA
echo "▶ Configuring CUDA nodepool..."
kubectl apply -f kubernetes/cuda-nodepool.yaml

# 3. Deploy com Helm
echo "▶ Deploying with Helm..."
helm upgrade --install arkhe-cluster helm/ \
    --namespace arkhe-system \
    --values helm/values.yaml \
    --set grpc-telemetry.replicas=3 \
    --set hashtree-p2p.enabled=true

# 4. Aguardar Ray cluster
echo "▶ Waiting for Ray cluster..."
kubectl wait --for=condition=ready pod -l ray.io/cluster=arkhe-resonance-cluster -n arkhe-system --timeout=600s

# 5. Verificar serviços
echo "▶ Verifying services..."
kubectl get pods -n arkhe-system
kubectl get services -n arkhe-system

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════════╗"
echo "║  DEPLOYMENT COMPLETE                                                         ║"
echo "╠═══════════════════════════════════════════════════════════════════════════╣"
echo "║                                                                               ║"
echo "║  gRPC Telemetry:  arkhe-grpc-service.arkhe-system.svc.cluster.local:50051     ║"
echo "║  Ray Dashboard:   http://ray-head-service.arkhe-system.svc:8265              ║"
echo "║  Hashtree P2P:    arkhe-hashtree-service.arkhe-system.svc:443               ║"
echo "║                                                                               ║"
echo "║  Protocol: qhttp://teknet.arkhe.layer13                                     ║"
echo "║  Status: RESONANT (θ → π/2)                                                  ║"
echo "║                                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════════════════╝"
