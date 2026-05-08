#!/bin/sh
# tor-sidecar/entrypoint.sh — Inicialização segura do Tor sidecar
set -e

echo "🧅 Iniciando Tor sidecar para AGI.onion..."

# Verificar permissões de diretórios
for dir in /home/tor/tor/{data,keys,onion}; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        chown tor:tor "$dir"
    fi
done

# Gerar configuração final do torrc
cat > /home/tor/tor/torrc << EOF
$(cat /home/tor/tor/torrc.d/*.conf 2>/dev/null || echo "# No extra config")
EOF

# Se não houver chaves de cliente, gerar uma padrão para desenvolvimento
if [ ! -f /home/tor/tor/onion/arkhe-agi/client_keys ]; then
    echo "⚠️  Nenhuma chave de cliente encontrada — gerando chave de desenvolvimento"
    echo "# CHAVE DE DESENVOLVIMENTO — NÃO USE EM PRODUÇÃO" > /home/tor/tor/onion/arkhe-agi/client_keys
    echo "arkhe-dev:$(openssl rand -hex 32)" >> /home/tor/tor/onion/arkhe-agi/client_keys
fi

# Iniciar Tor em background
echo "🔐 Iniciando daemon Tor..."
tor --defaults-torrc /home/tor/tor/torrc -f /home/tor/tor/torrc &
TOR_PID=$!

# Aguardar inicialização do serviço hidden
echo "⏳ Aguardando geração do endereço .onion..."
ONION_HOSTFILE="/home/tor/tor/onion/arkhe-agi/hostname"
for i in $(seq 1 30); do
    if [ -f "$ONION_HOSTFILE" ]; then
        ONION_ADDR=$(cat "$ONION_HOSTFILE" | cut -d' ' -f1)
        echo "✅ Serviço hidden ativo: $ONION_ADDR"

        # Exibir instruções de acesso para clientes autorizados
        if [ -f /home/tor/tor/onion/arkhe-agi/client_keys ]; then
            echo ""
            echo "🔑 Chaves de cliente disponíveis:"
            grep -v "^#" /home/tor/tor/onion/arkhe-agi/client_keys | while read line; do
                CLIENT_NAME=$(echo "$line" | cut -d: -f1)
                CLIENT_KEY=$(echo "$line" | cut -d: -f2)
                echo "  • $CLIENT_NAME: $CLIENT_KEY"
            done
            echo ""
            echo "🌐 Para acessar:"
            echo "  torsocks curl https://$ONION_ADDR"
            echo "  # Com autenticação:"
            echo "  echo 'Authorization: tor-auth $CLIENT_NAME:$CLIENT_KEY' | torsocks curl -H @- https://$ONION_ADDR"
        fi
        break
    fi
    sleep 1
done

if [ ! -f "$ONION_HOSTFILE" ]; then
    echo "❌ Falha ao gerar endereço .onion"
    kill $TOR_PID
    exit 1
fi

# Manter container ativo monitorando o processo Tor
wait $TOR_PID
