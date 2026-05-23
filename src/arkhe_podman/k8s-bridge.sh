#!/bin/bash
set -euo pipefail

POD_NAME="${1:-arkhe-pod}"
OUTPUT_FILE="${2:-arkhe-k8s.yaml}"

if ! podman pod exists "$POD_NAME"; then
    echo "ERRO: Pod '$POD_NAME' não encontrado."
    exit 1
fi

podman generate kube "$POD_NAME" > "$OUTPUT_FILE"

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