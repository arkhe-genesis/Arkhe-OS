#!/bin/bash
# scripts/sign_packages.sh — Assinatura Criptográfica de Pacotes ARKHE OS
# Substrate 318: Sovereign Package Signer

set -e

# Configurações
GPG_KEY_ID="${GPG_KEY_ID:-arkhe-os-signing@arkhe.os}"
COSIGN_KEY="${COSIGN_KEY:-cosign.key}"
REKOR_SERVER="${REKOR_SERVER:-https://rekor.sigstore.dev}"
OUTPUT_DIR="${OUTPUT_DIR:-dist/signed}"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

usage() {
    cat << EOF
Usage: $0 [OPTIONS] <package_files...>

Assina pacotes ARKHE OS usando múltiplos métodos criptográficos.

Options:
  -g, --gpg-only          Usar apenas assinatura GPG
  -c, --cosign-only       Usar apenas assinatura cosign (Sigstore)
  -a, --all               Usar todos os métodos (padrão)
  -v, --verify            Verificar assinaturas após assinar
  -o, --output DIR        Diretório de saída (padrão: dist/signed)
  -h, --help              Mostrar esta ajuda

Supported formats: .deb, .rpm, .tar.gz, Docker images

Examples:
  $0 arkhe-agi-core_1.0.0_amd64.deb
  $0 --cosign-only my-image:latest
  $0 --verify --all *.deb *.rpm
EOF
    exit 1
}

# Parse arguments
SIGN_GPG=true
SIGN_COSIGN=true
VERIFY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -g|--gpg-only)
            SIGN_GPG=true
            SIGN_COSIGN=false
            shift
            ;;
        -c|--cosign-only)
            SIGN_GPG=false
            SIGN_COSIGN=true
            shift
            ;;
        -a|--all)
            SIGN_GPG=true
            SIGN_COSIGN=true
            shift
            ;;
        -v|--verify)
            VERIFY=true
            shift
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        -*)
            log_error "Unknown option: $1"
            usage
            ;;
        *)
            PACKAGES+=("$1")
            shift
            ;;
    esac
done

if [ ${#PACKAGES[@]} -eq 0 ]; then
    log_error "No packages specified"
    usage
fi

# Criar diretório de saída
mkdir -p "$OUTPUT_DIR"

# ============================================================
# FUNÇÕES DE ASSINATURA
# ============================================================

sign_deb_gpg() {
    local deb_file="$1"
    log_info "Assinando .deb com GPG: $deb_file"

    if ! command -v dpkg-sig &> /dev/null; then
        log_error "dpkg-sig não encontrado. Instale com: sudo apt install dpkg-sig"
        return 1
    fi

    # Assinar o pacote
    dpkg-sig --sign builder --key "$GPG_KEY_ID" "$deb_file"

    # Verificar se solicitado
    if $VERIFY; then
        if dpkg-sig --verify "$deb_file" &> /dev/null; then
            log_info "✅ Assinatura GPG verificada: $deb_file"
        else
            log_error "❌ Verificação GPG falhou: $deb_file"
            return 1
        fi
    fi
}

sign_rpm_gpg() {
    local rpm_file="$1"
    log_info "Assinando .rpm com GPG: $rpm_file"

    if ! command -v rpm &> /dev/null; then
        log_error "rpm não encontrado"
        return 1
    fi

    # Assinar o pacote
    rpm --addsign "$rpm_file"

    # Verificar se solicitado
    if $VERIFY; then
        if rpm --checksig "$rpm_file" &> /dev/null; then
            log_info "✅ Assinatura GPG verificada: $rpm_file"
        else
            log_error "❌ Verificação GPG falhou: $rpm_file"
            return 1
        fi
    fi
}

sign_cosign() {
    local artifact="$1"
    local artifact_type="$2"  # container, file, etc.

    log_info "Assinando com cosign: $artifact ($artifact_type)"

    if ! command -v cosign &> /dev/null; then
        log_error "cosign não encontrado. Instale de: https://docs.sigstore.dev/cosign/installation/"
        return 1
    fi

    case $artifact_type in
        container)
            # Assinar imagem Docker/OCI
            cosign sign --yes \
                --key "$COSIGN_KEY" \
                --tlog-upload=true \
                --rekor-url "$REKOR_SERVER" \
                "$artifact"
            ;;
        file)
            # Assinar arquivo genérico via blob
            cosign sign-blob --yes \
                --key "$COSIGN_KEY" \
                --tlog-upload=true \
                --rekor-url "$REKOR_SERVER" \
                --output-signature "${artifact}.sig" \
                --output-certificate "${artifact}.cert" \
                "$artifact"
            ;;
        *)
            log_error "Tipo de artefato não suportado: $artifact_type"
            return 1
            ;;
    esac

    # Verificar se solicitado
    if $VERIFY; then
        case $artifact_type in
            container)
                if cosign verify --key "${COSIGN_KEY}.pub" "$artifact" &> /dev/null; then
                    log_info "✅ Assinatura cosign verificada: $artifact"
                else
                    log_error "❌ Verificação cosign falhou: $artifact"
                    return 1
                fi
                ;;
            file)
                if cosign verify-blob --key "${COSIGN_KEY}.pub" \
                    --signature "${artifact}.sig" \
                    --certificate "${artifact}.cert" \
                    "$artifact" &> /dev/null; then
                    log_info "✅ Assinatura cosign verificada: $artifact"
                else
                    log_error "❌ Verificação cosign falhou: $artifact"
                    return 1
                fi
                ;;
        esac
    fi
}

generate_checksums() {
    local input_dir="$1"
    local output_file="${OUTPUT_DIR}/SHA256SUMS"

    log_info "Gerando checksums SHA256..."

    # Limpar arquivo anterior
    > "$output_file"

    # Gerar checksums para todos os arquivos
    find "$input_dir" -type f \( -name "*.deb" -o -name "*.rpm" -o -name "*.tar.gz" \) | \
        while read -r file; do
            sha256sum "$file" >> "$output_file"
        done

    # Assinar o arquivo de checksums com GPG
    if $SIGN_GPG; then
        gpg --detach-sign --armor --key "$GPG_KEY_ID" "$output_file"
        log_info "✅ SHA256SUMS assinado com GPG"
    fi

    log_info "✅ Checksums gerados: $output_file"
}

# ============================================================
# PROCESSAMENTO PRINCIPAL
# ============================================================

log_info "🔐 Iniciando processo de assinatura para ${#PACKAGES[@]} artefatos"

for package in "${PACKAGES[@]}"; do
    if [ ! -f "$package" ]; then
        log_warn "Arquivo não encontrado: $package"
        continue
    fi

    # Copiar para diretório de saída
    cp "$package" "$OUTPUT_DIR/"
    signed_file="${OUTPUT_DIR}/$(basename "$package")"

    # Determinar tipo de arquivo
    case "$package" in
        *.deb)
            $SIGN_GPG && sign_deb_gpg "$signed_file"
            $SIGN_COSIGN && sign_cosign "$signed_file" "file"
            ;;
        *.rpm)
            $SIGN_GPG && sign_rpm_gpg "$signed_file"
            $SIGN_COSIGN && sign_cosign "$signed_file" "file"
            ;;
        *.tar.gz|*.tar.xz)
            $SIGN_COSIGN && sign_cosign "$signed_file" "file"
            ;;
        *:*)  # Docker image reference (contains :)
            $SIGN_COSIGN && sign_cosign "$package" "container"
            ;;
        *)
            log_warn "Formato não reconhecido: $package"
            continue
            ;;
    esac
done

# Gerar arquivo de checksums consolidado
generate_checksums "$OUTPUT_DIR"

# Relatório final
echo ""
echo "============================================================"
echo "🔐 ASSINATURA CONCLUÍDA"
echo "============================================================"
echo "Artefatos processados: ${#PACKAGES[@]}"
echo "Diretório de saída: $OUTPUT_DIR"
echo ""
echo "Arquivos gerados:"
ls -lh "$OUTPUT_DIR" | grep -E '\.(deb|rpm|tar\.gz|sig|asc|cert)$' || echo "  (nenhum)"
echo ""
echo "Para verificar:"
echo "  # Verificar GPG:"
echo "  gpg --verify ${OUTPUT_DIR}/SHA256SUMS.asc ${OUTPUT_DIR}/SHA256SUMS"
echo "  sha256sum -c ${OUTPUT_DIR}/SHA256SUMS"
echo ""
echo "  # Verificar cosign:"
echo "  cosign verify --key cosign.pub <artifact>"
echo "============================================================"

exit 0