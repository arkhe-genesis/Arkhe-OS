#!/bin/bash
# install.sh — Configuração do ambiente rootless Podman para ARKHE OS

echo "🏛️ Configurando ambiente rootless Podman..."

# Verificar podman instalado
if ! command -v podman &> /dev/null; then
    echo "❌ Podman não encontrado. Instale com: sudo apt install podman"
    exit 1
fi

# Criar usuário AGI se não existir
if ! id "agi" &>/dev/null; then
    sudo useradd -m -s /bin/bash agi
    echo "✅ Usuário 'agi' criado"
fi

# Configurar subuid/subgid para rootless
if ! grep -q "agi:" /etc/subuid; then
    echo "agi:100000:65536" | sudo tee -a /etc/subuid
    echo "agi:100000:65536" | sudo tee -a /etc/subgid
fi

# Habilitar linger para o usuário agi (inicialização após boot)
sudo loginctl enable-linger agi

# Copiar serviço systemd
mkdir -p /home/agi/.config/systemd/user/
cp agi/system32/container/podman/arkhe-agi-podman.service /home/agi/.config/systemd/user/
chown -R agi:agi /home/agi/.config

# Instalar e ativar o serviço como usuário agi
sudo -u agi bash -c "
    systemctl --user daemon-reload
    systemctl --user enable arkhe-agi-podman.service
    systemctl --user start arkhe-agi-podman.service
"

echo "✅ Ambiente Podman rootless configurado"
echo "   Verifique com: sudo -u agi systemctl --user status arkhe-agi-podman"
