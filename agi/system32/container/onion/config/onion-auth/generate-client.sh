#!/bin/bash
# generate-client.sh — Gera credenciais de autenticação para clientes Tor
set -e

CLIENT_NAME="${1:-arkhe-client-$(date +%s)}"
OUTPUT_DIR="${2:-./client-keys}"

mkdir -p "$OUTPUT_DIR"

# Gerar chave de autenticação (formato: nome:chave_hex_64chars)
CLIENT_KEY=$(openssl rand -hex 32)
CREDENTIAL="$CLIENT_NAME:$CLIENT_KEY"

# Adicionar ao arquivo de chaves do serviço hidden
ONION_KEYS_DIR="${3:-/home/tor/tor/onion/arkhe-agi}"
mkdir -p "$ONION_KEYS_DIR"

# Atualizar torrc se necessário
if ! grep -q "HiddenServiceAuthorizeClient" "$ONION_KEYS_DIR/../torrc" 2>/dev/null; then
    echo "HiddenServiceAuthorizeClient stealth $CLIENT_NAME" >> "$ONION_KEYS_DIR/../torrc"
    echo "⚠️  Reinicie o serviço Tor para aplicar a nova configuração"
fi

# Salvar credencial
echo "$CREDENTIAL" >> "$OUTPUT_DIR/${CLIENT_NAME}.key"
chmod 600 "$OUTPUT_DIR/${CLIENT_NAME}.key"

# Gerar instruções de uso para o cliente
cat > "$OUTPUT_DIR/${CLIENT_NAME}-instructions.txt" << EOF
# Credenciais para acesso a AGI.onion
# =====================================

Endereço do serviço: https://<onion_address>.onion
Nome do cliente: $CLIENT_NAME
Chave de autenticação: $CLIENT_KEY

# Exemplo de acesso via curl + torsocks:
export TOR_AUTH="$CLIENT_NAME:$CLIENT_KEY"
echo "Authorization: tor-auth \$TOR_AUTH" | torsocks curl -H @- https://<onion_address>.onion/health

# Exemplo em Python (com stem e requests):
from stem import Signal
from stem.control import Controller
import requests

with Controller.from_port(port=9051) as controller:
    controller.authenticate()
    controller.signal(Signal.NEWNYM)  # Novo circuito

session = requests.Session()
session.proxies = {
    'http': 'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050',
}
session.headers['Authorization'] = f'tor-auth $CREDENTIAL'

response = session.get('https://<onion_address>.onion/health')
print(response.json())
EOF

echo "✅ Credenciais geradas para $CLIENT_NAME"
echo "   Arquivos:"
echo "   • $OUTPUT_DIR/${CLIENT_NAME}.key (chave secreta — proteja!)"
echo "   • $OUTPUT_DIR/${CLIENT_NAME}-instructions.txt (instruções de uso)"
echo ""
echo "⚠️  Para ativar a nova chave no serviço:"
echo "   1. Copie $OUTPUT_DIR/${CLIENT_NAME}.key para o diretório de chaves do servidor"
echo "   2. Reinicie o serviço Tor: podman pod restart arkhe-agi-onion"