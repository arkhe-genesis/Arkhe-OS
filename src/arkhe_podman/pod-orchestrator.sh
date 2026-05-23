#!/bin/bash
set -euo pipefail

POD_NAME="arkhe-pod"
NETWORK_NAME="arkhe-net"

if ! podman network exists "$NETWORK_NAME"; then
    podman network create "$NETWORK_NAME" --subnet 10.89.0.0/24
fi

if podman pod exists "$POD_NAME"; then
    podman pod rm -f "$POD_NAME"
fi

podman pod create \
    --name "$POD_NAME" \
    --network "$NETWORK_NAME" \
    --publish 8080:8080 \
    --publish 8443:8443 \
    --infra \
    --label "arkhe.substrate=587" \
    --label "arkhe.seal=2d927c2c115e87a7130bf0bb01ec8725852a4dea40fe1d944e3c355c27e96370"

podman run -d \
    --pod "$POD_NAME" \
    --name "arkhe-runtime" \
    --label "arkhe.role=runtime" \
    -v "$(pwd)/arkhe:/arkhe:Z" \
    arkhe:v∞.Ω.∇+++

podman run -d \
    --pod "$POD_NAME" \
    --name "arkhe-health" \
    --label "arkhe.role=healthcheck" \
    --restart=always \
    alpine:latest \
    sh -c "while true; do wget -qO- http://localhost:8080/health || echo 'FAIL'; sleep 30; done"

podman run -d \
    --pod "$POD_NAME" \
    --name "arkhe-tlsnotary" \
    --label "arkhe.role=notary" \
    --restart=always \
    -v "$(pwd)/proofs:/proofs:Z" \
    tlsnotary/tlsn:latest