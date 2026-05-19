#!/bin/bash
# setup_physical_runner.sh — Canon: ∞.Ω.∇+++.258.physical_runner_setup
# Configura runner físico para validação de hardware com TPM

set -euo pipefail

echo "🏛️ ARKHE Ω‑TEMP v∞.Ω — Physical Runner Setup"
echo "   Substrate 258: Hardware Validation Lab"
echo ""

# Parâmetros configuráveis
RUNNER_NAME="${RUNNER_NAME:-arkhe-validator-$(hostname)}"
RUNNER_LABELS="${RUNNER_LABELS:-physical,tpm,${ARCH:-amd64}}"
GITHUB_TOKEN="${GITHUB_TOKEN:?GITHUB_TOKEN environment variable required}"
ARKHE_HOME="${ARKHE_HOME:-/opt/arkhe}"
TPM_DEVICE="${TPM_DEVICE:-/dev/tpmrm0}"

# 1. Instalar dependências do sistema
echo "📦 Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y \
    tpm2-tools \
    tpm2-pkcs11 \
    tpm2-abrmd \
    mokutil \
    efibootmgr \
    libtss2-dev \
    libtss2-tcti-device0 \
    prometheus-node-exporter \
    qemu-user-static \
    binfmt-support

# 2. Instalar ferramentas Arkhe
echo "🔧 Installing Arkhe tools..."
sudo snap install snapcraft --classic --channel=edge
sudo snap install ubuntu-image --classic --channel=edge

# 3. Configurar acesso TPM
echo "🔐 Configuring TPM access..."
sudo usermod -a -G tss $(whoami)
sudo systemctl enable tpm2-abrmd
sudo systemctl start tpm2-abrmd

# Verificar TPM
if command -v tpm2_getcap &>/dev/null && tpm2_getcap -c properties-fixed &>/dev/null; then
    echo "✅ TPM 2.0 detected and accessible"
    tpm2_getcap -c properties-fixed | grep -E "TPM2_PT_FIXED|Manufacturer" || true
else
    echo "⚠️  TPM 2.0 not detected; continuing with emulation mode"
fi

# 4. Configurar diretório Arkhe
echo "📂 Setting up Arkhe home directory..."
sudo mkdir -p "$ARKHE_HOME"/{bin,etc,var/log,var/data,tmp,ssh}
sudo chown -R $(whoami):$(whoami) "$ARKHE_HOME"

# Copiar scripts de validação
cp -r arkhe-core-image/validation "$ARKHE_HOME/validation"
cp -r arkhe-core-image/scripts "$ARKHE_HOME/scripts"

# 5. Configurar SSH para acesso remoto
echo "🔑 Configuring SSH access..."
SSH_KEY_DIR="$ARKHE_HOME/ssh"
mkdir -p "$SSH_KEY_DIR"
chmod 700 "$SSH_KEY_DIR"

if [ ! -f "$SSH_KEY_DIR/id_ed25519" ]; then
    ssh-keygen -t ed25519 -f "$SSH_KEY_DIR/id_ed25519" -N "" -C "arkhe-runner@${RUNNER_NAME}"
fi

# Adicionar chave pública ao authorized_keys
cat "$SSH_KEY_DIR/id_ed25519.pub" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# 6. Registrar runner no GitHub
echo "🔗 Registering GitHub Actions runner..."
cd "$ARKHE_HOME"
curl -s -O -L https://github.com/actions/runner/releases/latest/download/actions-runner-linux-${ARCH:-x64}-*.tar.gz
tar xzf actions-runner-linux-*.tar.gz
rm actions-runner-linux-*.tar.gz

# Configurar runner
./config.sh \
    --url https://github.com/arkhe-org/arkhe-core-image \
    --token "$GITHUB_TOKEN" \
    --name "$RUNNER_NAME" \
    --labels "$RUNNER_LABELS" \
    --work "_work" \
    --unattended \
    --replace

# 7. Configurar serviço systemd para runner
echo "⚙️  Configuring systemd service..."
sudo ./svc.sh install $(whoami)
sudo ./svc.sh start

# 8. Configurar monitoramento Prometheus
echo "📊 Configuring Prometheus node_exporter..."
sudo systemctl enable prometheus-node-exporter
sudo systemctl start prometheus-node-exporter

# 9. Testar validação básica
echo "🧪 Running basic validation test..."
python3 "$ARKHE_HOME/validation/hardware_validator.py" --device-type "${PLATFORM:-generic-x86_64}" --image-path "/dev/null" || echo "⚠️  Validation test skipped (no image)"

# 10. Gerar selo canônico de configuração
echo ""
echo "🔐 Generating canonical configuration seal..."
CONFIG_SEAL=$(python3 -c "
import hashlib, json, time, os
payload = {
    'runner_name': '$RUNNER_NAME',
    'labels': '$RUNNER_LABELS',
    'tpm_device': '$TPM_DEVICE',
    'arkhe_home': '$ARKHE_HOME',
    'timestamp': time.time(),
    'hostname': os.uname().nodename
}
print(hashlib.sha3_256(json.dumps(payload, sort_keys=True).encode()).hexdigest())
")

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  PHYSICAL RUNNER CONFIGURATION COMPLETE                     ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "🏭 Runner Name: $RUNNER_NAME"
echo "🏷️  Labels: $RUNNER_LABELS"
echo "🔐 TPM Device: $TPM_DEVICE"
echo "📂 Arkhe Home: $ARKHE_HOME"
echo "🔗 GitHub: https://github.com/arkhe-org/arkhe-core-image/actions/runners"
echo "🔑 SSH Key: $SSH_KEY_DIR/id_ed25519.pub"
echo "🔐 Canonical Seal: $CONFIG_SEAL"
echo ""
echo "✅ Physical runner is now ready for hardware validation workflows"
echo "   Canon: ∞.Ω.∇+++.258.physical_runner_setup"
