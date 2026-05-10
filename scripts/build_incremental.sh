#!/usr/bin/env bash
# scripts/build_incremental.sh — Build incremental com cache de artefatos
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
CACHE_DIR="${PROJECT_ROOT}/.build-cache"
FEATURES="${FEATURES:-std}"

echo "⚡ ARKHE OS v168.1 — Build Incremental"
echo "Features: ${FEATURES}"
echo "Cache dir: ${CACHE_DIR}"

# Calcular cache key
CACHE_KEY=$(cargo run --quiet --bin arkhe-unified --features incremental-build -- --print-cache-key 2>/dev/null || \
             echo "fallback_$(date +%s)")

echo "Cache key: ${CACHE_KEY:0:16}..."

# Verificar se artefato já existe no cache
CACHED_BINARY="${CACHE_DIR}/${CACHE_KEY}/arkhe-unified"
if [[ -x "${CACHED_BINARY}" ]]; then
    echo "✅ Artefato encontrado no cache! Copiando..."
    mkdir -p "${PROJECT_ROOT}/target/release"
    cp "${CACHED_BINARY}" "${PROJECT_ROOT}/target/release/arkhe-unified"
    echo "✅ Build concluído em $(date +%s.%N - $(cat ${CACHE_DIR}/${CACHE_KEY}/build_time 2>/dev/null || echo $(date +%s)))s (do cache)"
else
    # Build real
    echo "🔨 Compilando (cache miss)..."
    START_TIME=$(date +%s)

    cargo build --release --features "${FEATURES}" --target x86_64-unknown-linux-gnu

    END_TIME=$(date +%s)
    BUILD_TIME=$((END_TIME - START_TIME))

    # Armazenar no cache
    mkdir -p "${CACHE_DIR}/${CACHE_KEY}"
    cp "${PROJECT_ROOT}/target/x86_64-unknown-linux-gnu/release/arkhe-unified" "${CACHE_DIR}/${CACHE_KEY}/"
    echo "${BUILD_TIME}" > "${CACHE_DIR}/${CACHE_KEY}/build_time"

    echo "✅ Build concluído em ${BUILD_TIME}s"
    echo "💾 Artefato armazenado no cache"

    # Limpar cache antigo
    echo "🧹 Limpando cache expirado..."
    cargo run --quiet --bin arkhe-unified --features incremental-build -- --cleanup-cache 2>/dev/null || true
fi
