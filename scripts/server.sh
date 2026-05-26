#!/bin/bash
# ============================================================
# server.sh — llama.cpp server launcher
# Usage: ./server.sh [--gpu]
# ============================================================
set -euo pipefail

# ── Configuration (override via environment) ────────────────
MODEL_PATH="${MODEL_PATH:-./models/model.gguf}"
LLAMA_CPP_PATH="${LLAMA_CPP_PATH:-./llama.cpp}"
CONTEXT_LENGTH="${CONTEXT_LENGTH:-4096}"
THREADS="${THREADS:-$(nproc)}"
GPU_LAYERS="${GPU_LAYERS:-0}"
PORT="${PORT:-8080}"
HOST="${HOST:-127.0.0.1}"
PARALLEL="${PARALLEL:-4}"       # simultaneous request slots
LOG_DIR="${LOG_DIR:-./logs}"

# ── Parse flags ─────────────────────────────────────────────
USE_GPU=false
while [[ $# -gt 0 ]]; do
    case "$1" in
        --gpu)   USE_GPU=true; GPU_LAYERS="${GPU_LAYERS:-35}"; shift ;;
        --port)  PORT="$2"; shift 2 ;;
        --model) MODEL_PATH="$2"; shift 2 ;;
        --ctx)   CONTEXT_LENGTH="$2"; shift 2 ;;
        -h|--help)
            echo "Usage: $0 [--gpu] [--port PORT] [--model PATH] [--ctx N]"
            exit 0 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# ── Pre-flight checks ────────────────────────────────────────
SERVER_BIN="$LLAMA_CPP_PATH/build/bin/llama-server"

if [[ ! -f "$MODEL_PATH" ]]; then
    echo "[ERROR] Model not found: $MODEL_PATH"
    echo "  Download a GGUF model and set MODEL_PATH, e.g.:"
    echo "  MODEL_PATH=./models/llama-3-8b-Q4_K_M.gguf $0"
    exit 1
fi

if [[ ! -f "$SERVER_BIN" ]]; then
    echo "[ERROR] llama-server binary not found: $SERVER_BIN"
    echo "  Build llama.cpp first:"
    echo "    git clone https://github.com/ggerganov/llama.cpp $LLAMA_CPP_PATH"
    echo "    cmake -B $LLAMA_CPP_PATH/build $LLAMA_CPP_PATH && cmake --build $LLAMA_CPP_PATH/build -j"
    exit 1
fi

# ── Compute model seal ───────────────────────────────────────
mkdir -p "$LOG_DIR"
if command -v sha3sum &>/dev/null; then
    MODEL_SEAL=$(sha3sum "$MODEL_PATH" | cut -d' ' -f1)
elif command -v python3 &>/dev/null; then
    MODEL_SEAL=$(python3 -c "
import hashlib, sys
with open('$MODEL_PATH','rb') as f:
    h = hashlib.sha3_256()
    for chunk in iter(lambda: f.read(65536), b''):
        h.update(chunk)
    print(h.hexdigest())
")
else
    MODEL_SEAL="(sha3 unavailable)"
fi

# ── Print config ─────────────────────────────────────────────
echo "============================================================"
echo "  LLM Server"
echo "============================================================"
echo "  Model:      $MODEL_PATH"
echo "  Seal:       ${MODEL_SEAL:0:32}..."
echo "  Context:    $CONTEXT_LENGTH tokens"
echo "  Threads:    $THREADS"
echo "  GPU layers: $GPU_LAYERS"
echo "  Parallel:   $PARALLEL slots"
echo "  Bind:       $HOST:$PORT"
echo "  Logs:       $LOG_DIR"
echo "============================================================"

# ── Build server arguments ───────────────────────────────────
SERVER_ARGS=(
    -m "$MODEL_PATH"
    -c "$CONTEXT_LENGTH"
    -t "$THREADS"
    --port "$PORT"
    --host "$HOST"
    --parallel "$PARALLEL"
    --metrics               # expose /metrics endpoint
    --log-format json
    --flash-attn            # enable flash attention (faster, lower VRAM)
)

if [[ "$USE_GPU" == "true" ]] && [[ "$GPU_LAYERS" -gt 0 ]]; then
    SERVER_ARGS+=(--n-gpu-layers "$GPU_LAYERS")
fi

# ── Set library path and launch ──────────────────────────────
export LD_LIBRARY_PATH="$LLAMA_CPP_PATH/build/bin${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

LOG_FILE="$LOG_DIR/server_$(date +%Y%m%d_%H%M%S).log"
echo "[INFO] Logging to: $LOG_FILE"
echo "[INFO] Starting server..."

exec "$SERVER_BIN" "${SERVER_ARGS[@]}" 2>&1 | tee -a "$LOG_FILE"
