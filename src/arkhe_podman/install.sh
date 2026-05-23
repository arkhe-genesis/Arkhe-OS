#!/bin/bash
# arkhe-podman/install.sh
# Substrate 587-PODMAN-RUNTIME — Instalador Automático
# Compatível: Debian 12+, Ubuntu 22.04+, Fedora 38+, RHEL 9+

set -euo pipefail

ARKHE_VERSION="v∞.Ω.∇+++"
SUBSTRATE_ID="587"
SEAL="2d927c2c115e87a7130bf0bb01ec8725852a4dea40fe1d944e3c355c27e96370"
USER_UID="${ARKHE_UID:-1000}"
USER_GID="${ARKHE_GID:-1000}"

echo "═══════════════════════════════════════════════════════════"
echo "ARKHE OS $ARKHE_VERSION — Substrate $SUBSTRATE_ID PODMAN-RUNTIME"
echo "Selo: $SEAL"
echo "═══════════════════════════════════════════════════════════"

# 1. Verificar Podman instalado
if ! command -v podman &> /dev/null; then
    echo "[1/5] Instalando Podman..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y podman podman-compose
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y podman podman-compose
    elif command -v yum &> /dev/null; then
        sudo yum install -y podman podman-compose
    else
        echo "ERRO: Gerenciador de pacotes não suportado"
        exit 1
    fi
else
    echo "[1/5] Podman já instalado: $(podman --version)"
fi

# 2. Verificar user namespaces (rootless requirement)
echo "[2/5] Verificando suporte a user namespaces..."
if [[ ! -f /proc/sys/kernel/unprivileged_userns_clone ]] || \
   [[ $(cat /proc/sys/kernel/unprivileged_userns_clone 2>/dev/null) -ne 1 ]]; then
    echo "AVISO: User namespaces podem não estar habilitados."
    echo "Execute: sudo sysctl kernel.unprivileged_userns_clone=1"
fi

# 3. Criar utilizador arkhe (rootless)
echo "[3/5] Configurando utilizador arkhe (UID=$USER_UID)..."
if ! id -u arkhe &> /dev/null; then
    sudo useradd -u "$USER_UID" -g "$USER_GID" -m -s /bin/bash arkhe || true
fi

# 4. Configurar subuid/subgid para rootless
ARKHE_USER="arkhe"
echo "[4/5] Configurando subuid/subgid..."
if ! grep -q "^$ARKHE_USER:" /etc/subuid 2>/dev/null; then
    echo "$ARKHE_USER:100000:65536" | sudo tee -a /etc/subuid
    echo "$ARKHE_USER:100000:65536" | sudo tee -a /etc/subgid
fi

# 5. Gerar systemd service
SERVICE_FILE="/etc/systemd/system/arkhe.service"
echo "[5/5] Gerando systemd service..."
sudo tee "$SERVICE_FILE" > /dev/null <<INNEREOF
[Unit]
Description=ARKHE OS $ARKHE_VERSION (Podman Runtime)
Documentation=https://arkhe-os.org/docs/587-podman-runtime
Wants=network-online.target
After=network-online.target

[Service]
Environment=PODMAN_SYSTEMD_UNIT=%n
Restart=always
RestartSec=5
Type=notify
NotifyAccess=all
User=$ARKHE_USER
Group=$ARKHE_USER

ExecStart=/usr/bin/podman run \
    --cgroups=split \
    --rm \
    --sdnotify=conmon \
    --replace \
    --name arkhe-runtime \
    -v /opt/arkhe/data:/arkhe/data:Z \
    -p 8080:8080 \
    arkhe:$ARKHE_VERSION

ExecStop=/usr/bin/podman stop -t 30 arkhe-runtime
ExecStopPost=/usr/bin/podman rm -f arkhe-runtime

[Install]
WantedBy=default.target
INNEREOF

sudo systemctl daemon-reload
sudo systemctl enable arkhe.service

echo ""
echo "✓ Instalação concluída!"
echo "  Serviço: systemctl start arkhe"
echo "  Status:  systemctl status arkhe"
echo "  Logs:    journalctl -u arkhe -f"
echo ""
echo "Para build da imagem:"
echo "  podman build -t arkhe:$ARKHE_VERSION -f Podmanfile ."