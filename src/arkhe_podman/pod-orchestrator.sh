#!/bin/bash
# arkhe-podman/pod-orchestrator.sh
# Substrate 587-PODMAN-RUNTIME — Pod Orchestrator
# Cria um pod Arkhe com múltiplos containers

set -euo pipefail

POD_NAME="arkhe-pod"
NETWORK_NAME="arkhe-net"

echo "═══════════════════════════════════════════════════════════"
echo "ARKHE OS Pod Orchestrator — Substrate 587"
echo "═══════════════════════════════════════════════════════════"

# 1. Criar network dedicada (se não existir)
if ! podman network exists "$NETWORK_NAME"; then
    echo "[1/4] Criando network $NETWORK_NAME..."
    podman network create "$NETWORK_NAME" --subnet 10.89.0.0/24
fi

# 2. Criar pod
if podman pod exists "$POD_NAME"; then
    echo "[2/4] Removendo pod existente..."
    podman pod rm -f "$POD_NAME"
fi

echo "[2/4] Criando pod $POD_NAME..."
podman pod create \
    --name "$POD_NAME" \
    --network "$NETWORK_NAME" \
    --publish 8080:8080 \
    --publish 8443:8443 \
    --infra \
    --label "arkhe.substrate=587" \
    --label "arkhe.seal=2d927c2c115e87a7130bf0bb01ec8725852a4dea40fe1d944e3c355c27e96370"

# 3. Adicionar containers ao pod

echo "[3/4] Adicionando containers..."

# 3.1 Runtime principal
podman run -d \
    --pod "$POD_NAME" \
    --name "arkhe-runtime" \
    --label "arkhe.role=runtime" \
    -v "$(pwd)/arkhe:/arkhe:Z" \
    arkhe:v∞.Ω.∇+++

# 3.2 Healthcheck sidecar
podman run -d \
    --pod "$POD_NAME" \
    --name "arkhe-health" \
    --label "arkhe.role=healthcheck" \
    --restart=always \
    alpine:latest \
    sh -c "while true; do wget -qO- http://localhost:8080/health || echo 'FAIL'; sleep 30; done"

# 3.3 TLSNotary sidecar (provas de integridade)
podman run -d \
    --pod "$POD_NAME" \
    --name "arkhe-tlsnotary" \
    --label "arkhe.role=notary" \
    --restart=always \
    -v "$(pwd)/proofs:/proofs:Z" \
    tlsnotary/tlsn:latest

# 4. Verificar status
echo "[4/4] Verificando pod..."
podman pod ps
podman ps --pod

echo ""
echo "✓ Pod $POD_NAME criado com sucesso!"
echo "  Containers: $(podman ps --pod --filter "pod=$POD_NAME" --format "{{.Names}}" | wc -l)"
echo "  Network: $NETWORK_NAME"
echo ""
echo "Comandos úteis:"
echo "  podman pod ps                    # listar pods"
echo "  podman pod stop $POD_NAME        # parar pod"
echo "  podman pod rm $POD_NAME          # remover pod"
echo "  podman generate kube $POD_NAME   # exportar para K8s"