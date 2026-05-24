#!/bin/bash
set -euo pipefail

ARKHE_VERSION="v∞.Ω.∇+++"
SUBSTRATE_ID="587"
SEAL="2d927c2c115e87a7130bf0bb01ec8725852a4dea40fe1d944e3c355c27e96370"
USER_UID="${ARKHE_UID:-1000}"
USER_GID="${ARKHE_GID:-1000}"

if ! command -v podman &> /dev/null; then
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y podman podman-compose
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y podman podman-compose
    elif command -v yum &> /dev/null; then
        sudo yum install -y podman podman-compose
    else
        exit 1
    fi
fi

if [[ ! -f /proc/sys/kernel/unprivileged_userns_clone ]] || \
   [[ $(cat /proc/sys/kernel/unprivileged_userns_clone 2>/dev/null) -ne 1 ]]; then
    echo "AVISO: User namespaces podem não estar habilitados."
fi

if ! id -u arkhe &> /dev/null; then
    sudo useradd -u "$USER_UID" -g "$USER_GID" -m -s /bin/bash arkhe || true
fi

ARKHE_USER="arkhe"
if ! grep -q "^$ARKHE_USER:" /etc/subuid 2>/dev/null; then
    echo "$ARKHE_USER:100000:65536" | sudo tee -a /etc/subuid
    echo "$ARKHE_USER:100000:65536" | sudo tee -a /etc/subgid
fi

SERVICE_FILE="/etc/systemd/system/arkhe.service"
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