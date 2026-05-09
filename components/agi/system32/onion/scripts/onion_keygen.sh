#!/bin/bash
# onion_keygen.sh — Geração e rotação de chaves .onion para o ARKHE OS AGI

echo "🔄 Rodando chaves do serviço oculto AGI.onion..."

# Executa o comando de rotação através do wrapper run.sh
SCRIPT_DIR="$(dirname "$0")"
"$SCRIPT_DIR/onion_run.sh" rotate

echo "✅ Rotação de chaves solicitada. Verifique o status com 'onion_run.sh status' para o novo endereço .onion"
