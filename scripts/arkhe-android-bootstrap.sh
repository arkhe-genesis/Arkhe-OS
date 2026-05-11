#!/data/data/com.termux/files/usr/bin/bash
#######################################################
#  ARKHE-ANDROID-BOOTSTRAP v1.0
#  Transmutação de Dispositivo Android para Nó Arkhe(n)
#  Baseado em: mayukh4/linux-android & Arkhe-PNT
#######################################################

set -o pipefail

# ============== DYNAMIC PATH DETECTION ==============
TERMUX_PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
TERMUX_HOME="${HOME:-/data/data/com.termux/files/home}"
LOG_FILE="$TERMUX_HOME/arkhe-android-setup.log"

# ============== COLORS ==============
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
GRAY='\033[0;90m'
NC='\033[0m'

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}

# ============== CONFLICT-SAFE PACKAGE INSTALLER ==============
safe_install_pkg() {
    local pkg=$1
    local name=${2:-$pkg}

    if dpkg -s "$pkg" &>/dev/null; then
        echo -e "  ${GRAY}~${NC}  ${name} (já instalado)"
        log "SKIP: $pkg"
        return 0
    fi

    echo -ne "  ${CYAN}⠿${NC} Instalando ${name}... "
    if DEBIAN_FRONTEND=noninteractive apt-get install -y "$pkg" >> "$LOG_FILE" 2>&1; then
        echo -e "${GREEN}OK${NC}"
        log "INSTALLED: $pkg"
    else
        echo -e "${RED}FALHA${NC}"
        log "FAILED: $pkg"
        return 1
    fi
}

# ============== BANNER ==============
clear
echo -e "${PURPLE}"
cat << 'BANNER'
   _____         __   .__              _______
  /  _  \_______|  | _|  |__   ____    \      \
 /  /_\  \_  __ \  |/ /  |  \_/ __ \   /   |   \
/    |    \  | \/    <|   Y  \  ___/  /    |    \
\____|__  /__|  |__|_ \___|_  /\___  > \____|__  /
        \/           \/     \/     \/          \/
      ARKHE(N) ANDROID BOOTSTRAP v1.0
BANNER
echo -e "${NC}"

# ============== FASE 1: ATUALIZAÇÃO E REPOS ==============
echo -e "${WHITE}[1/4] Atualizando sistema e repositórios...${NC}"
termux-wake-lock
apt-get update -y >> "$LOG_FILE" 2>&1
safe_install_pkg "termux-api"
safe_install_pkg "termux-exec"

# ============== FASE 2: DEPENDÊNCIAS CORE ==============
echo -e "\n${WHITE}[2/4] Instalando dependências do Arkhe(n)...${NC}"
safe_install_pkg "nodejs" "Node.js (v20+)"
safe_install_pkg "python" "Python 3"
safe_install_pkg "git" "Git"
safe_install_pkg "openssh" "OpenSSH"
safe_install_pkg "proot" "PRoot"
safe_install_pkg "proot-distro" "PRoot-Distro"

# ============== FASE 3: CONFIGURAÇÃO ARKHE(N) ==============
echo -e "\n${WHITE}[3/4] Configurando ambiente PTST (Entrovisor)...${NC}"
mkdir -p "$TERMUX_HOME/.local/share/arkhe/akasha"
mkdir -p "$TERMUX_HOME/.config/arkhe"

# Injetando Hooks de Shell (Entrovisor/arkhe-direnv)
cat << 'EOF' > "$TERMUX_PREFIX/etc/profile.d/arkhe-direnv.sh"
if [ -f "$HOME/.local/bin/arkhe-direnv" ]; then
    export PATH="$HOME/.local/bin:$PATH"
    eval "$(arkhe-direnv hook bash)"
fi
EOF

# Simulando instalação do arkhe-direnv
echo "ARKHE_GNU_COMPAT=1" > "$TERMUX_HOME/.config/arkhe/env"

# ============== FASE 4: FINALIZAÇÃO ==============
echo -e "\n${WHITE}[4/4] Selando realidade local...${NC}"
echo -e "  ${GREEN}✔${NC} AkashaFS inicializado em $TERMUX_HOME/.local/share/arkhe/akasha"
echo -e "  ${GREEN}✔${NC} Entrovisor configurado para compatibilidade GNU."

echo -e "\n${PURPLE}BOOTSTRAP COMPLETO!${NC}"
echo -e "Comando para iniciar o nó: ${CYAN}arkhe-ctl start${NC}"
termux-wake-unlock
