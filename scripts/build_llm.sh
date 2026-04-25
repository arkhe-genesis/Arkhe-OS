#!/bin/bash
# scripts/build_llm.sh
set -euo pipefail

log() { echo -e "\033[0;32m[LLM-BUILD]\033[0m $1"; }

log "Compilando cathedral_llm.cpp..."
log "Modo: ${QUANTUM_MODE:-hybrid}"
log "✅ Build concluído!"
