#!/bin/bash
# podman_build.sh — Build multi‑arch com podman/buildah
set -e

IMAGE="ghcr.io/arkhe-os/agi-core"
VERSION="${1:-latest}"
PLATFORMS="linux/amd64,linux/arm64,linux/ppc64le,linux/s390x,linux/riscv64"

echo "🔨 Construindo imagem multi‑arch: ${IMAGE}:${VERSION}"

# Usar buildah via podman para multi‑arch
for platform in $(echo "$PLATFORMS" | tr ',' ' '); do
    arch=$(echo "$platform" | cut -d'/' -f2)
    echo "  📦 Building: ${arch}..."
    podman build \
        --platform "$platform" \
        --tag "${IMAGE}:${arch}-${VERSION}" \
        --file agi/system32/container/podman/Containerfile \
        .
done

# Criar manifest multi‑arch e push
podman manifest create "${IMAGE}:${VERSION}"
for arch in amd64 arm64 ppc64le s390x riscv64; do
    podman manifest add "${IMAGE}:${VERSION}" "${IMAGE}:${arch}-${VERSION}"
done

echo "📤 Enviando para registry..."
podman manifest push --all "${IMAGE}:${VERSION}" "docker://${IMAGE}:${VERSION}"

echo "✅ Build e push concluídos"