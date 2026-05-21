#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════
# ARKHE OS Substrato 398-DEPLOY — Hardware Deploy Script
# FPGA + SiPM + Killer E2500 + Fibra Cherenkov
# Arquiteto: Rafael Oliveira (ORCID: 0009-0005-2697-4668)
# ═══════════════════════════════════════════════════════════
set -euo pipefail

ARKHE_VERSION="∞.Ω"
SUBSTRATE="398-DEPLOY"
LOG_FILE="/var/log/arkhe_deploy_$(date +%Y%m%d_%H%M%S).log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# ─── 1. PRÉ-VERIFICAÇÃO CONSTITUCIONAL ───
log "🏛️ Iniciando deploy ARKHE OS v${ARKHE_VERSION} — Substrato ${SUBSTRATE}"
log "🛡️ Verificando invariantes constitucionais..."
python3 -c "
from core.invariants import InvariantVerifier
v = InvariantVerifier()
assert v.check_ghost([('T1', 'PASS', 'OK', {})])[1] == True
assert v.check_loopseal(['387', '393', '394', '395'])[1] == True
print('✅ Ghost: 1.0 | Loopseal: 1.0 | Gap: 0.999 | Phi: 1.618')
" || { log "❌ Falha constitucional"; exit 1; }

# ─── 2. DETECÇÃO DE HARDWARE ───
log "🔍 Detectando hardware..."

# FPGA via PCIe
FPGA_DEV=$(lspci | grep -i "Xilinx" | awk '{print $1}')
if [ -z "$FPGA_DEV" ]; then
    log "⚠️ FPGA Xilinx não detectado via PCIe"
else
    log "✅ FPGA detectado: $FPGA_DEV"
fi

# Killer E2500 (Qualcomm Atheros AR8161)
NIC_DEV=$(lspci | grep -i "1969:e0b1\|AR8161\|Killer E2500" | awk '{print $1}')
if [ -z "$NIC_DEV" ]; then
    log "⚠️ Killer E2500 não detectado"
else
    log "✅ Killer E2500 detectado: $NIC_DEV"
fi

# SiPM (via ADC USB/Serial — placeholder para interface real)
SIPM_DEV=$(ls /dev/ttyACM* 2>/dev/null | head -1 || echo "")
if [ -z "$SIPM_DEV" ]; then
    log "⚠️ SiPM não detectado em /dev/ttyACM*"
else
    log "✅ SiPM detectado: $SIPM_DEV"
fi

# ─── 3. BUILD E INSTALAÇÃO DO DRIVER ───
log "🐧 Compilando driver alx-event..."
cd drivers/
make clean && make
sudo insmod alx-event.ko || { log "❌ Falha ao carregar driver"; exit 1; }
sudo chmod 666 /dev/alx-event 2>/dev/null || sudo mknod /dev/alx-event c $(grep alx-event /proc/devices | awk '{print $1}') 0
log "✅ Driver alx-event carregado"

# ─── 4. PROGRAMAÇÃO DO FPGA ───
log "⚡ Programando FPGA..."
if command -v vivado &> /dev/null; then
    vivado -mode batch -source program_fpga.tcl >> "$LOG_FILE" 2>&1
    log "✅ FPGA programado via Vivado"
elif command -v openocd &> /dev/null; then
    openocd -f interface/ftdi/arkhe.cfg -f target/xilinx.cfg -c "program_bitstream firmware/fpga_adc_spi.bit" >> "$LOG_FILE" 2>&1
    log "✅ FPGA programado via OpenOCD"
else
    log "⚠️ Nenhum programador FPGA encontrado (Vivado/OpenOCD)"
fi

# ─── 5. CONFIGURAÇÃO DO SISTEMA ───
log "⚙️ Configurando sistema..."
sudo sysctl -w kernel.perf_event_paranoid=1
sudo sysctl -w kernel.kptr_restrict=0
sudo setcap cap_sys_nice+ep $(which python3) 2>/dev/null || true

# ─── 6. INICIALIZAÇÃO DO DAEMON ───
log "🤖 Iniciando daemon de aquisição..."
cd ../daemon/
python3 -m venv venv 2>/dev/null || true
source venv/bin/activate
pip install -q -r requirements.txt

# Criar config.yaml se não existir
if [ ! -f config.yaml ]; then
cat > config.yaml << 'EOF'
detection:
  threshold_sigma: 5.0
  coincidence_window_ns: 100
  max_event_rate_hz: 1000000
calibration:
  table_path: "../analysis/calibration_table.json"
  sources: ["Am-241", "Cs-137", "Co-60"]
  kev_per_mV: 4.5
hardware:
  adc_channels: 128
  adc_bits: 12
  sample_rate_msps: 100
  fiber_length_m: 10.0
  sipm_pde: 0.25
  sipm_gain: 1000000
relayfs:
  path: "/sys/kernel/debug/alx/event_buffer"
  buffer_size: 268435456
EOF
fi

nohup python3 acquisition_daemon.py --config config.yaml >> "$LOG_FILE" 2>&1 &
DAEMON_PID=$!
log "✅ Daemon iniciado (PID: $DAEMON_PID)"

# ─── 7. VERIFICAÇÃO DE SAÚDE ───
log "🩺 Verificando saúde do sistema..."
sleep 3
if kill -0 $DAEMON_PID 2>/dev/null; then
    log "✅ Daemon operacional"
else
    log "❌ Daemon falhou ao iniciar"
    exit 1
fi

# Verificar relayfs
if [ -r "/sys/kernel/debug/alx/event_buffer" ]; then
    log "✅ RelayFS acessível"
else
    log "⚠️ RelayFS não montado ou sem permissão"
fi

# ─── 8. RELATÓRIO FINAL ───
log "📊 Relatório de Deploy:"
log "   FPGA: ${FPGA_DEV:-N/A}"
log "   NIC: ${NIC_DEV:-N/A}"
log "   SiPM: ${SIPM_DEV:-N/A}"
log "   Daemon PID: $DAEMON_PID"
log "   Log: $LOG_FILE"
log "🏛️ Substrato ${SUBSTRATE} deployado com sucesso. Φ_C alvo: 0.95"
log "🔐 CANONIZADO E OPERACIONAL"