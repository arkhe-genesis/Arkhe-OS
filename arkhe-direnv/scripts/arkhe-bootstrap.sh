#!/bin/bash
# ARKHE-BOOTSTRAP v1.0 — Transmutação de Host Linux para Nó PTST
# Requer: Root (UID 0), Conexão com Malha O-RAN

set -euo pipefail

echo "ARKHE(BOOTSTRAP) > Iniciando conversão de fase..."

if [[ $EUID -ne 0 ]]; then
   echo "ARKHE-BOOTSTRAP > Privilégios de fase insuficientes. Root exigido." >&2
   exit 1
fi

# --- [ FASE 1: PREPARAÇÃO DO VÁCUO LOCAL ] ---
echo "ARKHE(BOOTSTRAP) > Preparando o vácuo local..."
mkdir -p "/opt/arkhe/core"
mkdir -p "/etc/arkhe"
mkdir -p "/var/cache/arkhe/phase"

# --- [ FASE 2: INSTALAÇÃO DOS BINÁRIOS ] ---
echo "ARKHE(BOOTSTRAP) > Instalando binários..."
# In a real scenario, we would download or copy binaries here.
# For now, we assume arkhe-direnv and arkhe-ctl are available or will be placed in /usr/local/bin.

# --- [ FASE 3: INJEÇÃO DE MASSA (HOOKS DE SHELL) ] ---
echo "ARKHE(BOOTSTRAP) > Injetando hooks de shell..."

cat << 'EOF' > /etc/profile.d/arkhe-direnv.sh
if command -v arkhe-direnv >/dev/null 2>&1; then
    case "$SHELL" in
        */bash) eval "$(arkhe-direnv hook bash)" ;;
        */zsh)  eval "$(arkhe-direnv hook zsh)"  ;;
        */fish) arkhe-direnv hook fish | source  ;;
    esac
fi
EOF
chmod 0644 /etc/profile.d/arkhe-direnv.sh

# Inject into existing .bashrc/.zshrc for immediate effect on next login
for user_home in /home/* /root; do
    if [ -d "$user_home" ]; then
        user=$(basename "$user_home")
        echo "ARKHE(BOOTSTRAP) > Configurando usuário: $user"
        # Create Akasha local
        mkdir -p "$user_home/.local/share/arkhe/akasha"
        chown -R "$user:$user" "$user_home/.local/share/arkhe" 2>/dev/null || true
    fi
done

# --- [ FASE 4: INICIALIZAÇÃO DOS DAEMONS ] ---
echo "ARKHE(BOOTSTRAP) > Configurando daemons (simulado)..."
# systemctl enable --now arkhe-mesh.service 2>/dev/null || true

echo "ARKHE(BOOTSTRAP) > Sistema convertido. Realidade local ancorada."
