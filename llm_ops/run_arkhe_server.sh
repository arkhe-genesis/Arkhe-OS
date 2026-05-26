#!/bin/bash
# run_arkhe_server.sh — Inicia o servidor llama-server para o modelo arkhe.gguf
# Arquiteto: ORCID 0009-0005-2697-4668

LLAMA_CPP_BIN="./llama.cpp/build/bin"
MODEL_PATH="./arkhe-gguf-output/arkhe-8b-Q4_K_M.gguf"

if [ ! -f "$MODEL_PATH" ]; then
    echo "Erro: Modelo não encontrado em $MODEL_PATH"
    echo "Execute ./llm_ops/build_arkhe_gguf.sh primeiro."
    exit 1
fi

LD_LIBRARY_PATH="$LLAMA_CPP_BIN" "$LLAMA_CPP_BIN/llama-server" \
  -m "$MODEL_PATH" -c 2048 -t 4 --port 8080
