#!/usr/bin/env bash
# install.sh — Cross-Platform ARKHE OS .agi Handler Installer
# Substrato 5003: Universal File Association
#
# Usage: curl -fsSL https://arkhe.os/install-agi-handler.sh | bash

set -euo pipefail

# ─── Configuration ─────────────────────────────────────────────
readonly ARKHE_VERSION="5003.1.0"
readonly DEFAULT_PREFIX="${XDG_DATA_HOME:-$HOME/.local}/arkhe"
PREFIX="${PREFIX:-$DEFAULT_PREFIX}"
USER_MODE="${USER_MODE:-true}"
SKIP_ICONS="${SKIP_ICONS:-false}"

# ─── Color Output ──────────────────────────────────────────────
readonly RED='\033[0;31m' GREEN='\033[0;32m' YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m' CYAN='\033[0;36m' NC='\033[0m'

log() { echo -e "${BLUE}[ARKHE]${NC} $1"; }
success() { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1" >&2; }

# ─── OS Detection ──────────────────────────────────────────────
detect_os() {
    case "$(uname -s)" in
        Linux)
            [[ -f /etc/alpine-release ]] && echo "alpine" && return
            [[ -f /etc/debian_version ]] && echo "debian" && return
            [[ -f /etc/redhat-release ]] && echo "rhel" && return
            echo "linux-generic" ;;
        Darwin) echo "macos" ;;
        FreeBSD|OpenBSD|NetBSD) echo "bsd" ;;
        CYGWIN*|MINGW*|MSYS*) echo "windows" ;;
        *) echo "unknown" ;;
    esac
}

OS="$(detect_os)"
log "Detected OS: ${OS}"

# ─── Platform-Specific Installation ────────────────────────────
install_platform() {
    case "$OS" in
        windows)
            log "Windows detected — delegating to PowerShell"
            if command -v powershell.exe &>/dev/null; then
                powershell.exe -NoProfile -ExecutionPolicy Bypass \
                    -File "$(dirname "$0")/windows/install.ps1" \
                    -InstallPath "${PREFIX//\//\\}" \
                    ${SKIP_ICONS:+-SkipIcons} ${USER_MODE:+-UserMode}
            else
                error "PowerShell not available. Run windows/install.ps1 manually."
                exit 1
            fi ;;
        macos)
            log "macOS detected"
            bash "$(dirname "$0")/macos/install.sh" --prefix="$PREFIX" \
                ${USER_MODE:+--user} ${SKIP_ICONS:+--skip-icons} ;;
        linux|alpine|debian|rhel|linux-generic)
            log "Linux detected"
            bash "$(dirname "$0")/linux/install.sh" --prefix="$PREFIX" \
                --distro="$OS" ${USER_MODE:+--user} ${SKIP_ICONS:+--skip-icons} ;;
        bsd)
            log "BSD detected"
            bash "$(dirname "$0")/bsd/install.sh" --prefix="$PREFIX" \
                ${USER_MODE:+--user} ;;
        *)
            error "Unsupported platform: $OS"
            exit 1 ;;
    esac
}

# ─── Pre-Install Checks ────────────────────────────────────────
check_prerequisites() {
    log "Checking prerequisites..."
    command -v python3 &>/dev/null || { error "Python 3.8+ required"; exit 1; }
    command -v tar &>/dev/null || { error "tar required for extraction"; exit 1; }
    success "Prerequisites satisfied"
}

# ─── Main ─────────────────────────────────────────────────────
main() {
    log "🪟🍎🐧 ARKHE OS .agi Handler v$ARKHE_VERSION"
    log "Platform: $OS | Prefix: $PREFIX | User mode: $USER_MODE"

    check_prerequisites
    install_platform

    echo ""
    success "Installation complete!"
    echo "  • Double-click any .agi file to open"
    echo "  • Run 'agictl --help' for CLI usage"
    echo "  • Docs: https://arkhe.os/docs/agi-artifacts"
}

main "$@"
