#!/bin/bash
# =============================================================================
# setup_3mac_demo.sh — Configuração completa da demo com 3 MacBooks
# =============================================================================
# Uso: Execute em cada MacBook com a variável ROLE definida:
#
#   ROLE=ALFA  ./setup_3mac_demo.sh
#   ROLE=BETA  ./setup_3mac_demo.sh
#   ROLE=GAMMA ./setup_3mac_demo.sh
#
# Pré-requisitos:
#   - macOS com Homebrew
#   - Python 3.10+
#   - Ollama instalado e rodando
#   - Este script no mesmo diretório em todos os MacBooks
# =============================================================================

set -euo pipefail

# ── Detecção automática de IP ──────────────────────────────────────────────

ROLE="${ROLE:?Defina ROLE=ALFA, BETA ou GAMMA}"
IP=$(ipconfig getifaddr en0 || ifconfig en0 | grep "inet " | awk '{print $2}')

echo "═══════════════════════════════════════════════════════════════"
echo "  ARKHE Ω-TEMP v4.0 — Setup 3-MacBook Demo"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "  Papel:      ${ROLE}"
echo "  IP local:   ${IP}"
echo "  Hostname:   $(hostname)"
echo "  macOS:      $(sw_vers -productVersion 2>/dev/null || echo 'N/A')"
echo "  Python:     $(python3 --version)"
echo ""

# ── Configuração por papel ─────────────────────────────────────────────────

case "$ROLE" in
    ALFA)
        NODE_ID="ALFA-01"
        TIP_PORT=9501
        GW_PORT=8081
        DS4_PORT=12341
        AI_ROUTING=false
        PEERS='["192.168.1.20:9502"]'
        ;;
    BETA)
        NODE_ID="BETA-02"
        TIP_PORT=9502
        GW_PORT=8082
        DS4_PORT=12342
        AI_ROUTING=true
        PEERS='["192.168.1.10:9501", "192.168.1.30:9503"]'
        ;;
    GAMMA)
        NODE_ID="GAMMA-03"
        TIP_PORT=9503
        GW_PORT=8083
        DS4_PORT=12343
        AI_ROUTING=false
        PEERS='["192.168.1.20:9502"]'
        ;;
    *)
        echo "ERRO: ROLE deve ser ALFA, BETA ou GAMMA"
        exit 1
        ;;
esac

# ── Instalação de dependências ─────────────────────────────────────────────

echo "[1/6] Verificando dependências..."

install_pkg() {
    if ! brew list "$1" &>/dev/null; then
        echo "  Instalando $1..."
        brew install "$1" --quiet
    else
        echo "  ✓ $1 já instalado"
    fi
}

install_pkg python3
install_pkg ollama
install_pkg coreutils

# NumPy via pip
python3 -m pip install numpy --quiet 2>/dev/null || echo "  (numpy já instalado)"

# Ollama: iniciar se não estiver rodando
if ! pgrep -x "ollama" > /dev/null; then
    echo "  Iniciando Ollama..."
    ollama serve > /dev/null 2>&1 &
    sleep 3
fi

# Baixar modelo se necessário
MODEL_PRESENT=$(ollama list 2>/dev/null | grep -c "llama3.1" || echo "0")
if [ "$MODEL_PRESENT" -eq 0 ]; then
    echo "  Baixando modelo llama3.1..."
    ollama pull llama3.1
else
    echo "  ✓ Modelo llama3.1 disponível"
fi

echo ""

# ── Criação do banco de ledger ────────────────────────────────────────────

echo "[2/6] Inicializando ledger temporal..."

python3 << 'PYEOF'
import sqlite3, json, hashlib, time
from pathlib import Path

import sys
role = sys.argv[1]

db_path = Path(f"/tmp/arkhe_{role}.db")
conn = sqlite3.connect(str(db_path))
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("""CREATE TABLE IF NOT EXISTS ledger_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    timestamp REAL NOT NULL,
    hash TEXT NOT NULL UNIQUE
)""")
conn.execute("CREATE INDEX IF NOT EXISTS idx_type ON ledger_entries(event_type)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_ts ON ledger_entries(timestamp)")

payload = json.dumps({
    'node_id': role,
    'event': 'demo_initialization',
    'version': '4.0.0',
    'role': role,
    'timestamp': time.time()
}, sort_keys=True)
h = hashlib.sha3_256(payload.encode()).hexdigest()
conn.execute("INSERT INTO ledger_entries (event_type, payload_json, timestamp, hash) VALUES (?,?,?,?)",
    ('node_demo_init', payload, time.time(), h))
conn.commit()
conn.close()
print(f"  ✓ Ledger /tmp/arkhe_{role}.db criado")
PYEOF

# ── Início do ds4-server ───────────────────────────────────────────────────

echo "[3/6] Configurando ds4-server..."

# Verificar se ds4-real está instalado
if command -v ds4server &>/dev/null; then
    ds4server --port "$DS4_PORT" --sensors accel,gyro,light,touch &
    DS4_PID=$!
    echo "  ds4-server iniciado (PID $DS4_PID, porta $DS4_PORT)"
    echo "  $DS4_PID" > "/tmp/ds4_${NODE_ID}.pid"
else
    echo "  ⚠ ds4-server não encontrado. Instale: npm install -g ds4-real"
    echo "  Continuando sem ds4..."
fi

echo ""

# ── Início do nó temporal ──────────────────────────────────────────────────

echo "[4/6] Iniciando nó temporal ${NODE_ID}..."

# Gerar argumentos de AI routing
AI_ARGS=""
if [ "$AI_ROUTING" = true ]; then
    AI_ARGS="--ai-routing --ai-paradox-check --ai-content-filter --model llama3.1"
fi

# Iniciar o nó em background
python3 -c "
import sys
sys.path.insert(0, '.')
from temporal_network_v4_final import RetroNode, TAddr, RetroNet, TemporalRouter
import threading, time, json

node = RetroNode('${NODE_ID}', taddr=TAddr.from_parts('${NODE_ID}', time.time(), 0.001))

# Iniciar
node.start()

# Se for BETA, ativar AI router
if '${AI_ROUTING}' == 'True':
    from ai_augmented_router import AIRouter, AIConfig
    config = AIConfig(endpoint='http://localhost:11434', model='llama3.1:8b')
    ai = AIRouter(node.router, node._channel, config)

    # Substituir process handler
    original_process = node.router.process
    def ai_process(pkt, addr):
        return ai.process_packet(pkt, addr)
    node.router.process = ai_process
    print(f'🤖 AI Router ativo no nó ${NODE_ID}')

print(f'✅ Nó ${NODE_ID} operacional em {node.taddr}')

# Manter rodando
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    node.stop()
" > "/tmp/arkhe_${NODE_ID}.log" 2>&1 &

NODE_PID=$!
echo "  Nó temporal iniciado (PID $NODE_PID)"
echo "  Log: /tmp/arkhe_${NODE_ID}.log"
echo "  Gateway: http://localhost:${GW_PORT}"
echo "  TIP Port: ${TIP_PORT}"
echo "  $NODE_PID" > "/tmp/arkhe_${NODE_ID}.pid"

# ── Esperar inicialização ─────────────────────────────────────────────────

echo ""
echo "[5/6] Aguardando inicialização..."

for i in {1..30}; do
    if curl -s --max-time 1 "http://localhost:${GW_PORT}/health" &>/dev/null || \
       curl -s --max-time 1 "http://localhost:${TIP_PORT}/health" &>/dev/null 2>&1; then
        echo "  ✓ Nó ${NODE_ID} respondendo ✓"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "  ⚠ Timeout — verifique /tmp/arkhe_${NODE_ID}.log"
    fi
    sleep 0.5
done

# ── Status final ───────────────────────────────────────────────────────────

echo ""
echo "[6/6] Status do Nó ${ROLE}:"
echo "═══════════════════════════════════════════════════════════════"
echo "  Nó:      ${NODE_ID}"
echo "  IP:      ${IP}"
echo "  TIP:     porta ${TIP_PORT}"
echo "  Gateway: porta ${GW_PORT}"
echo "  DS4:     porta ${DS4_PORT}"
echo "  AI:      $([ "$AI_ROUTING" = true ] && echo '✓ Llama 3.1' || echo '✗ Heurístico')"
echo "  Ledger:  /tmp/arkhe_${NODE_ID}.db"
echo "  PID:     $NODE_PID"
echo ""
echo "  Parar:   kill $NODE_PID $([ -f /tmp/ds4_${NODE_ID}.pid ] && cat /tmp/ds4_${NODE_ID}.pid || true)"
echo ""

# ── Instruções de uso ──────────────────────────────────────────────────────

if [ "$ROLE" = "ALFA" ]; then
    echo "═══════════════════════════════════════════════════════════════"
    echo "  🎮 INSTRUÇÕES DE USO — DEMO RETROCASUAL"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    echo "  Nesta demo, ALFA (você) envia mensagens para GAMMA passando por BETA."
    echo "  BETA usa AI Router (Llama 3.1) para:"
    echo "    • Escolher a melhor rota"
    echo "    • Verificar paradoxos temporais"
    echo "    • Filtrar conteúdo suspeito"
    echo ""
    echo "  1. Envie uma mensagem para o futuro (+120 segundos):"
    echo ""
    echo "     python3 -c \"
import sys; sys.path.insert(0, '.')
from temporal_network_v4_final import *
node = RetroNode('ALFA-01')
node.start()
time.sleep(1)
# Conectar ao BETA
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
ta = TAddr.from_parts('BETA-02', time.time(), 0.001)
node.connect_peer(type('P',(),{'nid':'BETA-02','taddr':ta,'send':lambda a,b,c: None,'receive':lambda a,b: None})())
node.send_message('GAMMA-03', 'Olá do futuro via BETA com AI!', target_time=time.time()+120)
print('Mensagem enviada!')
\"
"
    echo ""
    echo "  2. Ver status da rede:"
    echo "     curl http://localhost:${GW_PORT}/status"
    echo ""
    echo "  3. Verificar cadeia temporal:"
    echo "     sqlite3 /tmp/arkhe_ALFA.db 'SELECT event_type, timestamp, hash FROM ledger_entries ORDER BY id DESC LIMIT 10;'"
    echo ""
    echo "  4. Ver logs do BETA (AI decisions):"
    echo "     tail -f /tmp/arkhe_BETA.log"
    echo ""
fi