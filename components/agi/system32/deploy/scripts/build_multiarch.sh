#!/bin/bash
# scripts/build_multiarch.sh — Build Multi-Arquitetura para ARKHE OS
# Substrate 318: Universal Architecture Builder

set -e

# Configurações padrão
ARCHS="${ARCHS:-amd64 arm64 riscv64}"
OUTPUT_DIR="${OUTPUT_DIR:-dist}"
DOCKER_PUSH="${DOCKER_PUSH:-false}"
QEMU_SETUP="${QEMU_SETUP:-true}"

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[BUILD]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Constrói artefatos ARKHE OS para múltiplas arquiteturas.

Options:
  -a, --archs LIST     Arquiteturas para build (padrão: amd64 arm64 riscv64)
  -o, --output DIR     Diretório de saída (padrão: dist)
  -p, --push           Push Docker images para registry
  -n, --no-qemu        Não configurar QEMU para emulação
  -c, --clean          Limpar builds anteriores antes de começar
  -h, --help           Mostrar esta ajuda

Supported architectures:
  amd64    - x86-64 (Intel/AMD)
  arm64    - ARM 64-bit (Apple M1/M2, AWS Graviton, Raspberry Pi 4+)
  riscv64  - RISC-V 64-bit (experimental)

Examples:
  $0 --archs amd64,arm64
  $0 --push --archs all
  $0 --clean --archs riscv64
EOF
    exit 1
}

# Parse arguments
CLEAN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -a|--archs)
            if [[ "$2" == "all" ]]; then
                ARCHS="amd64 arm64 riscv64"
            else
                ARCHS="${2//,/ }"
            fi
            shift 2
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -p|--push)
            DOCKER_PUSH=true
            shift
            ;;
        -n|--no-qemu)
            QEMU_SETUP=false
            shift
            ;;
        -c|--clean)
            CLEAN=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            error "Unknown option: $1"
            usage
            ;;
    esac
done

# ============================================================
# FUNÇÕES DE BUILD
# ============================================================

setup_qemu() {
    if $QEMU_SETUP; then
        log "Configurando QEMU para emulação multi-arch..."

        if ! command -v docker &> /dev/null; then
            warn "Docker não encontrado - pulando configuração QEMU"
            return
        fi

        docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
        success "QEMU configurado para emulação"
    fi
}

setup_buildx() {
    log "Configurando Docker Buildx..."

    if ! docker buildx version &> /dev/null; then
        error "Docker Buildx não encontrado"
        exit 1
    fi

    # Criar ou usar builder existente
    if ! docker buildx inspect arkhe-builder &> /dev/null; then
        docker buildx create --name arkhe-builder --driver docker-container --use
        success "Builder 'arkhe-builder' criado"
    else
        docker buildx use arkhe-builder
        log "Usando builder existente: arkhe-builder"
    fi

    # Bootstrap builder
    docker buildx inspect --bootstrap > /dev/null
}

build_ffis_for_arch() {
    local arch="$1"
    log "Compilando FFI bridges para $arch..."

    # Mapear arquitetura para flags de compilação
    case "$arch" in
        amd64)
            CC_FLAGS="-m64"
            PYTHON_CONFIG="python3.11-config"
            ;;
        arm64)
            CC_FLAGS="-march=armv8-a"
            PYTHON_CONFIG="aarch64-linux-gnu-python3.11-config"
            ;;
        riscv64)
            CC_FLAGS="-march=rv64gc"
            PYTHON_CONFIG="riscv64-linux-gnu-python3.11-config"
            ;;
        *)
            warn "Arquitetura não suportada para cross-compilation: $arch"
            return 1
            ;;
    esac

    # Verificar toolchain
    if [[ "$arch" != "amd64" ]]; then
        if ! command -v "${PYTHON_CONFIG%%-config}" &> /dev/null; then
            warn "Toolchain para $arch não encontrada - usando fallback"
            PYTHON_CONFIG="python3.11-config"
        fi
    fi

    # Compilar ponte RCP
    log "  Compilando agi_rcp_bridge.so para $arch..."
    gcc -shared -fPIC -O2 $CC_FLAGS \
        -I/usr/include/python3.11 \
        -o "build/agi_rcp_bridge_${arch}.so" \
        agi/system32/runtime/quantum/rcp_bridge.c \
        -lpython3.11 -lm

    # Compilar ponte Omni
    log "  Compilando agi_omni_bridge.so para $arch..."
    gcc -shared -fPIC -O2 $CC_FLAGS \
        -I/usr/include/python3.11 \
        -o "build/agi_omni_bridge_${arch}.so" \
        agi/system32/runtime/quantum/omni_bridge.c \
        -lpython3.11 -lm

    success "FFI bridges compiladas para $arch"
}

build_docker_multiarch() {
    local platforms="$1"
    local push_flag=""

    if $DOCKER_PUSH; then
        push_flag="--push"
        log "Push habilitado para registry"
    else
        push_flag="--load"
        log "Build local (sem push)"
    fi

    log "Construindo imagem Docker para: $platforms"

    docker buildx build \
        --platform "$platforms" \
        $push_flag \
        --tag ghcr.io/arkhe-os/arkhe-agi-core:latest \
        --tag ghcr.io/arkhe-os/arkhe-agi-core:$(git describe --tags --always --dirty) \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        --cache-from type=gha \
        --cache-to type=gha,mode=max \
        .

    success "Imagem Docker construída"
}

build_native_packages() {
    local arch="$1"
    local version="${VERSION:-$(git describe --tags --always --dirty)}"

    log "Construindo pacotes nativos para $arch (v$version)..."

    # Criar diretório temporário
    local tmpdir=$(mktemp -d)
    local pkg_name="arkhe-agi-core"

    case "$arch" in
        amd64|arm64|riscv64)
            # Build .deb
            log "  Criando pacote .deb para $arch..."

            # Estrutura Debian
            mkdir -p "$tmpdir/DEBIAN"
            mkdir -p "$tmpdir/usr/lib/agi/system32"
            mkdir -p "$tmpdir/etc/agi"

            # Copiar arquivos
            cp -r agi/system32/config/* "$tmpdir/etc/agi/" 2>/dev/null || true
            cp build/agi_*_bridge_${arch}.so "$tmpdir/usr/lib/agi/system32/" 2>/dev/null || true

            # Arquivo de controle
            cat > "$tmpdir/DEBIAN/control" << EOF
Package: ${pkg_name}
Version: ${version}
Architecture: ${arch}
Maintainer: ARKHE OS Collective <arkhe@cathedral.os>
Description: ARKHE OS AGI Core Runtime
 Multi-architecture build of ARKHE OS AGI Core with
 Retrocausal Channel Protocol v2.0 and Omni-Architecture.
Depends: python3 (>= 3.8), libc6 (>= 2.28)
EOF

            # Construir pacote
            dpkg-deb --build "$tmpdir" "${OUTPUT_DIR}/${pkg_name}_${version}_${arch}.deb"

            # Build .rpm (se disponível)
            if command -v rpmbuild &> /dev/null; then
                log "  Criando pacote .rpm para $arch..."
                # (Implementação simplificada - em produção usar spec file completo)
                echo "⚠️  Build RPM simplificado para $arch"
            fi

            success "Pacotes nativos construídos para $arch"
            ;;
        *)
            warn "Formato de pacote não suportado para $arch"
            ;;
    esac

    # Limpar
    rm -rf "$tmpdir"
}

# ============================================================
# EXECUÇÃO PRINCIPAL
# ============================================================

log "🚀 Iniciando build multi-arquitetura"
log "Arquiteturas: $ARCHS"
log "Diretório de saída: $OUTPUT_DIR"

# Limpar se solicitado
if $CLEAN; then
    log "Limpando builds anteriores..."
    rm -rf build/ "$OUTPUT_DIR"
    mkdir -p build "$OUTPUT_DIR"
fi

# Setup
setup_qemu
setup_buildx

# Build loop por arquitetura
for arch in $ARCHS; do
    log "=========================================="
    log "Processando arquitetura: $arch"
    log "=========================================="

    # Compilar FFIs
    build_ffis_for_arch "$arch"

    # Construir pacotes nativos
    build_native_packages "$arch"
done

# Build Docker multi-arch (se todas as arquiteturas foram processadas)
if [[ "$ARCHS" =~ "amd64" ]] && [[ "$ARCHS" =~ "arm64" ]]; then
    docker_platforms=""
    for arch in $ARCHS; do
        case "$arch" in
            amd64) docker_platforms+="linux/amd64," ;;
            arm64) docker_platforms+="linux/arm64," ;;
            riscv64) docker_platforms+="linux/riscv64," ;;
        esac
    done
    docker_platforms="${docker_platforms%,}"  # Remover vírgula final

    build_docker_multiarch "$docker_platforms"
fi

# Relatório final
echo ""
echo "============================================================"
echo "🎉 BUILD MULTI-ARQUITETURA CONCLUÍDO"
echo "============================================================"
echo "Arquiteturas processadas: $ARCHS"
echo ""
echo "Artefatos gerados:"
find "$OUTPUT_DIR" -type f \( -name "*.deb" -o -name "*.rpm" -o -name "*.so" \) | \
    while read -r f; do echo "  • $(basename "$f")"; done
echo ""
echo "Imagens Docker:"
if $DOCKER_PUSH; then
    echo "  • ghcr.io/arkhe-os/arkhe-agi-core:latest (multi-arch)"
else
    echo "  • (build local - use --push para enviar ao registry)"
fi
echo ""
echo "Próximos passos:"
echo "  1. Assinar artefatos: ./scripts/sign_packages.sh $OUTPUT_DIR/*"
echo "  2. Testar em arquitetura alvo: docker run --platform linux/arm64 ..."
echo "  3. Publicar no registry: ./scripts/sign_packages.sh --push ..."
echo "============================================================"

exit 0