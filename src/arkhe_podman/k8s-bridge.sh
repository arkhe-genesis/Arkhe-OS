#!/bin/bash
# arkhe-podman/k8s-bridge.sh
# Substrate 587-PODMAN-RUNTIME — Podman-to-Kubernetes Bridge
# Exporta pod Arkhe para YAML Kubernetes

set -euo pipefail

POD_NAME="${1:-arkhe-pod}"
OUTPUT_FILE="${2:-arkhe-k8s.yaml}"

echo "═══════════════════════════════════════════════════════════"
echo "ARKHE OS K8s Bridge — Substrate 587"
echo "═══════════════════════════════════════════════════════════"

if ! podman pod exists "$POD_NAME"; then
    echo "ERRO: Pod '$POD_NAME' não encontrado."
    echo "Execute primeiro: ./pod-orchestrator.sh"
    exit 1
fi

echo "[1/3] Exportando pod $POD_NAME para Kubernetes YAML..."
podman generate kube "$POD_NAME" > "$OUTPUT_FILE"

echo "[2/3] Adicionando labels ARKHE..."
cat >> "$OUTPUT_FILE" <<INNEREOF
---
# ARKHE OS Annotations
metadata:
  annotations:
    arkhe.substrate.id: "587"
    arkhe.substrate.name: "PODMAN-RUNTIME"
    arkhe.seal.sha256: "2d927c2c115e87a7130bf0bb01ec8725852a4dea40fe1d944e3c355c27e96370"
    arkhe.phi_c: "0.973333"
    arkhe.dcs: "0.979444"
    arkhe.architect: "ORCID:0009-0005-2697-4668"
INNEREOF

echo "[3/3] Validando YAML..."
if command -v kubectl &> /dev/null; then
    kubectl apply --dry-run=client -f "$OUTPUT_FILE"
    echo "✓ YAML validado com sucesso!"
else
    echo "AVISO: kubectl não encontrado. YAML gerado mas não validado."
fi

echo ""
echo "Arquivo gerado: $OUTPUT_FILE"
echo ""
echo "Para deploy no Kubernetes:"
echo "  kubectl apply -f $OUTPUT_FILE"
echo ""
echo "Para testar localmente com Podman:"
echo "  podman play kube $OUTPUT_FILE"