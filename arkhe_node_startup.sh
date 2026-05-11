#!/bin/bash
# =============================================================================
# arkhe_node_startup.sh — Inicialização Automática do Nó ARKHE
# =============================================================================
# Lança ds4-server E temporal_router com flags corretas para o ledger temporal.
# Uso:
#   ./arkhe_node_startup.sh <NODE_ID> [--ds4-only | --temporal-only]
#
# Exemplo:
#   ./arkhe_node_startup.sh ALFA-01
#   ./arkhe_node_startup.sh BETA-02 --temporal-only   (sem DualSense)
# =============================================================================

set -euo pipefail

# ── Configurações ──────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NODE_ID="${1:-ARKHE-01}"
MODE="${2:---full}"  # --full | --ds4-only | --temporal-only

# Ledger
LEDGER_DB="/tmp/arkhe_${NODE_ID}.db"
LEDGER_EXPORT="${LEDGER_DB}.json"
LEDGER_WINDOW_SECONDS=$((5 * 365 * 24 * 3600))  # 5 anos (~157.7M segundos)

# Portas
DS4_PORT=12345
TIP_PORT=9500
GATEWAY_PORT=8080
TEMPORAL_LOG="/tmp/arkhe_${NODE_ID}.log"

# Modelo local
MODEL_ENDPOINT="${MODEL_ENDPOINT:-http://localhost:11434}"  # Ollama padrão
MODEL_NAME="${MODEL_NAME:-llama3.1:8b}"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# PIDs (para cleanup)
DS4_PID=""
TEMPORAL_PID=""

# ── Funções auxiliares ─────────────────────────────────────────────────────

log_info()  { echo -e "${BLUE}[INFO]${NC}  $(date '+%Y-%m-%d %H:%M:%S')  $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $(date '+%Y-%m-%d %H:%M:%S')  $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $(date '+%Y-%m-%d %H:%M:%S')  $*"; }
log_err()   { echo -e "${RED}[ERRO]${NC}  $(date '+%Y-%m-%d %H:%M:%S')  $*" >&2; }

cleanup() {
    log_info "Encerrando nó ${NODE_ID}..."
    if [ -n "$TEMPORAL_PID" ] && kill -0 "$TEMPORAL_PID" 2>/dev/null; then
        kill "$TEMPORAL_PID" 2>/dev/null || true
        wait "$TEMPORAL_PID" 2>/dev/null || true
        log_ok "Temporal router encerrado (PID ${TEMPORAL_PID})"
    fi
    if [ -n "$DS4_PID" ] && kill -0 "$DS4_PID" 2>/dev/null; then
        kill "$DS4_PID" 2>/dev/null || true
        wait "$DS4_PID" 2>/dev/null || true
        log_ok "ds4-server encerrado (PID ${DS4_PID})"
    fi
    # Exportar ledger snapshot ao sair
    export_ledger_snapshot
    log_ok "Nó ${NODE_ID} encerrado limpamente"
}

trap cleanup SIGINT SIGTERM EXIT

export_ledger_snapshot() {
    if [ -f "$LEDGER_DB" ]; then
        log_info "Exportando snapshot do ledger → ${LEDGER_EXPORT}"
        python3 -c "
import json, sqlite3
conn = sqlite3.connect('${LEDGER_DB}')
rows = conn.execute('SELECT event_type,payload_json,timestamp,hash FROM ledger_entries ORDER BY id').fetchall()
data = [{'type':r[0],'payload':json.loads(r[1]),'timestamp':r[2],'hash':r[3]} for r in rows]
with open('${LEDGER_EXPORT}', 'w') as f: json.dump(data, f, indent=2, ensure_ascii=False)
print(f'Exportados {len(data)} registros')
" 2>/dev/null || log_warn "Falha ao exportar ledger snapshot"
    fi
}

# ── Verificações prévias ───────────────────────────────────────────────────

log_info "═════════════════════════════════════════════════"
log_info "  ARKHE Ω-TEMP v4.0 — Inicialização do Nó"
log_info "═════════════════════════════════════════════════"
log_info "Nó:           ${NODE_ID}"
log_info "Ledger DB:    ${LEDGER_DB}"
log_info "Janela:       ${LEDGER_WINDOW_SECONDS}s (~5 anos)"
log_info "Modelo:       ${MODEL_NAME} @ ${MODEL_ENDPOINT}"
log_info "Portas:       DS4=${DS4_PORT}  TIP=${TIP_PORT}  GW=${GATEWAY_PORT}"

# Verificar Python
if ! command -v python3 &>/dev/null; then
    log_err "Python3 não encontrado. Instale: brew install python3"
    exit 1
fi
PYTHON=$(which python3)
log_ok "Python:       $($PYTHON --version 2>&1)"

# Verificar NumPy
if ! $PYTHON -c "import numpy" 2>/dev/null; then
    log_warn "NumPy não encontrado. Instalando..."
    $PYTHON -m pip install numpy --quiet
fi
log_ok "NumPy:        $($PYTHON -c 'import numpy; print(numpy.__version__)')"

# Verificar ds4-server
DS4_AVAILABLE=false
if command -v ds4server &>/dev/null; then
    DS4_AVAILABLE=true
    log_ok "ds4-server:   $(ds4server --version 2>/dev/null || echo 'encontrado')"
elif [ -f "/usr/local/bin/ds4real" ] || [ -f "$HOME/.local/bin/ds4real" ]; then
    DS4_AVAILABLE=true
    log_ok "ds4-server:   instalado"
else
    log_warn "ds4-server não encontrado — modo --ds4-only indisponível"
    if [ "$MODE" = "--ds4-only" ]; then
        exit 1
    fi
fi

# Verificar modelo local
MODEL_AVAILABLE=false
check_model() {
    if curl -s --max-time 5 "${MODEL_ENDPOINT}/api/tags" 2>/dev/null | grep -q '"name"'; then
        MODEL_AVAILABLE=true
        log_ok "Modelo local: ✓ disponível em ${MODEL_ENDPOINT}"
    fi
}
check_model

if [ "$MODEL_AVAILABLE" = false ] && [ "$MODE" != "--ds4-only" ]; then
    log_warn "Modelo local não detectado em ${MODEL_ENDPOINT}"
    log_warn "O roteador AI usará fallback heurístico"
fi

# ── Inicialização do Ledger ────────────────────────────────────────────────

log_info "Inicializando ledger temporal..."
if [ ! -f "$LEDGER_DB" ]; then
    $PYTHON -c "
import sqlite3
conn = sqlite3.connect('${LEDGER_DB}')
conn.execute('PRAGMA journal_mode=WAL')
conn.execute('''CREATE TABLE IF NOT EXISTS ledger_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    timestamp REAL NOT NULL,
    hash TEXT NOT NULL UNIQUE
)''')
conn.execute('CREATE INDEX IF NOT EXISTS idx_type ON ledger_entries(event_type)')
conn.execute('CREATE INDEX IF NOT EXISTS idx_ts ON ledger_entries(timestamp)')
conn.execute('''CREATE TABLE IF NOT EXISTS ledger_index (
    entry_hash TEXT PRIMARY KEY,
    entry_id INTEGER NOT NULL
)''')
# Registro de inicialização
import json, hashlib, time
init_payload = json.dumps({
    'node_id': '${NODE_ID}',
    'version': '4.0.0',
    'window_seconds': ${LEDGER_WINDOW_SECONDS},
    'model': '${MODEL_NAME}',
    'model_endpoint': '${MODEL_ENDPOINT}',
    'created_at': time.time()
}, sort_keys=True)
h = hashlib.sha3_256(init_payload.encode()).hexdigest()
conn.execute('INSERT INTO ledger_entries (event_type,payload_json,timestamp,hash) VALUES (?,?,?,?)',
    ('node_initialized', init_payload, time.time(), h))
conn.commit()
conn.close()
print('Ledger criado com sucesso')
"
    log_ok "Ledger criado: ${LEDGER_DB}"
else
    log_ok "Ledger existente: ${LEDGER_DB}"
fi

# ── Lançamento de ds4-server ──────────────────────────────────────────────

if [ "$MODE" != "--temporal-only" ] && [ "$DS4_AVAILABLE" = true ]; then
    log_info "Iniciando ds4-server na porta ${DS4_PORT}..."

    # Detecção de dispositivo Bluetooth
    BT_DEVICE=""
    if [ -d "/sys/class/input" ]; then
        for dev in /sys/class/input/event*/device/name; do
            if [ -f "$dev" ] && grep -qi "wireless" "$dev" 2>/dev/null; then
                BT_DEVICE=$(cat "$dev")
                break
            fi
        done
    fi

    if [ -n "$BT_DEVICE" ]; then
        log_info "Dispositivo Bluetooth detectado: ${BT_DEVICE}"
    fi

    # Lançar ds4-server
    ds4server \
        --port "${DS4_PORT}" \
        --log-level info \
        --mac "${DS4_MAC:-auto}" \
        --sensors accel,gyro,light,pressure,touch \
        --output-json \
        > "/tmp/ds4_${NODE_ID}.log" 2>&1 &
    DS4_PID=$!

    # Esperar conexão
    for i in {1..30}; do
        if curl -s --max-time 1 "http://localhost:${DS4_PID:-12345}/status" &>/dev/null; then
            log_ok "ds4-server ativo (PID ${DS4_PID})"
            break
        fi
        sleep 0.5
    done

    if ! kill -0 "$DS4_PID" 2>/dev/null; then
        log_warn "ds4-server falhou ao iniciar — verifique Bluetooth"
        DS4_PID=""
    fi
fi

# ── Lançamento do Temporal Router ─────────────────────────────────────────

if [ "$MODE" != "--ds4-only" ]; then
    log_info "Iniciando temporal_router (ARKHE Ω-TEMP v4.0)..."

    # Determinar topologia (peers) a partir do arquivo de rede
    PEER_CONFIG=""
    PEER_FINGERPRINT=""
    NETWORK_FILE="${SCRIPT_DIR}/network_${NODE_ID}.json"

    if [ -f "$NETWORK_FILE" ]; then
        log_info "Arquivo de rede encontrado: ${NETWORK_FILE}"
        # Extrair peers do JSON
        PEER_LIST=$(python3 -c "
import json, sys
with open('${NETWORK_FILE}') as f:
    data = json.load(f)
peers = data.get('peers', {})
node_peers = peers.get('${NODE_ID}', [])
print(','.join(node_peers))
" 2>/dev/null || echo "")
        if [ -n "$PEER_LIST" ]; then
            PEER_CONFIG="--peers ${PEER_LIST}"
            log_info "Peers configurados: ${PEER_LIST}"
        fi
    fi

    # Construir comando de inicialização
    ROUTER_CMD=(
        python3
        "${SCRIPT_DIR}/temporal_network_v4_final.py"
        --mode router
        --node-id "${NODE_ID}"
        --db "${LEDGER_DB}"
        --window-seconds "${LEDGER_WINDOW_SECONDS}"
        --model-endpoint "${MODEL_ENDPOINT}"
        --model-name "${MODEL_NAME}"
        --ds4-port "${DS4_PORT}"
        --tip-port "${TIP_PORT}"
        --gateway-port "${GATEWAY_PORT}"
        --log-level INFO
        ${PEER_CONFIG}
    )

    if [ "$MODEL_AVAILABLE" = false ]; then
        ROUTER_CMD+=(--fallback-routing)
        log_warn "Usando roteamento heurístico (modelo não disponível)"
    fi

    log_info "Comando: ${ROUTER_CMD[*]}"

    "${ROUTER_CMD[@]}" \
        > "$TEMPORAL_LOG" 2>&1 &
    TEMPORAL_PID=$!

    # Esperar inicialização
    for i in {1..30}; do
        if curl -s --max-time 1 "http://localhost:${GATEWAY_PORT}/health" &>/dev/null; then
            log_ok "Temporal Router ativo (PID ${TEMPORAL_PID})"
            break
        fi
        sleep 0.5
    done

    if ! kill -0 "$TEMPORAL_PID" 2>/dev/null; then
        log_err "Temporal Router falhou ao iniciar!"
        cat "$TEMPORAL_LOG" | tail -20
        exit 1
    fi
fi

# ── Status Final ───────────────────────────────────────────────────────────

echo ""
log_ok "═════════════════════════════════════════════════"
log_ok "  NÓ ${NODE_ID} OPERACIONAL"
log_ok "═════════════════════════════════════════════════"

if [ -n "$DS4_PID" ]; then
    echo "  🎮 ds4-server:     PID ${DS4_PID} (porta ${DS4_PORT})"
fi
if [ -n "$TEMPORAL_PID" ]; then
    echo "  🕰️  Temporal Router: PID ${TEMPORAL_PID} (porta ${TIP_PORT})"
    echo "  🌐 Gateway TIP:    http://localhost:${GATEWAY_PORT}"
fi
echo "  📒 Ledger:          ${LEDGER_DB}"
echo "  🤖 Modelo:         ${MODEL_NAME} (${MODEL_ENDPOINT})"
echo ""
echo "  Monitoramento:  tail -f ${TEMPORAL_LOG}"
echo "  Encerrar:       kill ${DS4_PID:-} ${TEMPORAL_PID:-}"
echo ""

# Manter script ativo (wait)
wait
