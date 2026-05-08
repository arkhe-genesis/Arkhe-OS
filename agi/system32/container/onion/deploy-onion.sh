#!/bin/bash
# deploy-onion.sh — Deploy do pod AGI.onion via Podman rootless
set -e

POD_NAME="arkhe-agi-onion"
POD_FILE="agi/system32/container/onion/agi-onion-pod.yaml"
USER="${USER:-agi}"

echo "🏛️ Deploy de AGI.onion via Podman rootless (usuário: $USER)"

# Verificar dependências
for cmd in podman yq; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "❌ $cmd não encontrado. Instale antes de continuar."
        exit 1
    fi
done

# Criar diretórios de estado se não existirem
for dir in /var/lib/agi/state /var/log/agi /etc/agi; do
    if [ ! -d "$dir" ]; then
        sudo mkdir -p "$dir"
        sudo chown "$USER:$USER" "$dir"
        echo "✅ Diretório criado: $dir"
    fi
done

# Gerar chaves de cliente se não existirem
AUTH_DIR="agi/system32/container/onion/config/onion-auth"
if [ ! -d "$AUTH_DIR/client-keys" ]; then
    echo "🔑 Gerando chaves de cliente de exemplo..."
    mkdir -p "$AUTH_DIR/client-keys"

    # Gerar 3 chaves de exemplo (admin, peer, public)
    for client in arkhe-admin arkhe-peer arkhe-public; do
        KEY=$(openssl rand -hex 32)
        echo "$client:$KEY" >> "$AUTH_DIR/client-keys/default.keys"
        echo "  • $client: $KEY"
    done
    echo "✅ Chaves geradas em $AUTH_DIR/client-keys/default.keys"
fi

# Copiar configuração Tor para o diretório de configuração do usuário
TOR_CONFIG_DIR="$HOME/.config/agi/torrc.d"
mkdir -p "$TOR_CONFIG_DIR"
cp agi/system32/container/onion/tor-sidecar/torrc.d/*.conf "$TOR_CONFIG_DIR/" 2>/dev/null || true

# Construir imagens se necessário (opcional)
if [[ "${1:-}" == "--build" ]]; then
    echo "🔨 Reconstruindo imagens..."
    ./agi/system32/container/onion/tor-sidecar/build.sh
    ./agi/system32/container/podman/build.sh
fi

# Deploy do pod
echo "🚀 Iniciando pod $POD_NAME..."
if podman pod exists "$POD_NAME" &>/dev/null; then
    echo "⚠️  Pod já existe — removendo versão anterior"
    podman pod rm -f "$POD_NAME"
fi

podman play kube "$POD_FILE" --pod-name "$POD_NAME"

# Aguardar inicialização
echo "⏳ Aguardando inicialização do serviço hidden..."
for i in $(seq 1 60); do
    ONION_FILE="$HOME/.local/share/containers/storage/volumes/${POD_NAME}_onion-keys/_data/arkhe-agi/hostname"
    if [ -f "$ONION_FILE" ]; then
        ONION_ADDR=$(cat "$ONION_FILE" | cut -d' ' -f1)
        echo ""
        echo "✅ AGI.onion ativo!"
        echo "🌐 Endereço: https://$ONION_ADDR"
        echo ""
        echo "🔑 Para acessar (com autenticação):"
        echo "  export TOR_AUTH='arkhe-admin:$(grep arkhe-admin $AUTH_DIR/client-keys/default.keys | cut -d: -f2)'"
        echo "  echo \"Authorization: tor-auth \$TOR_AUTH\" | torsocks curl -H @- https://$ONION_ADDR/health"
        echo ""
        echo "📊 Healthcheck local:"
        echo "  podman exec -it ${POD_NAME}-agi-core /healthcheck.sh"
        break
    fi
    sleep 1
done

# Registrar nó em DHT (opcional)
if [[ "${2:-}" == "--register" ]]; then
    echo "🌐 Registrando nó em registry descentralizado..."
    ./agi/system32/container/onion/register-node.sh "$ONION_ADDR"
fi

echo ""
echo "🎉 Deploy concluído!"
echo "   Gerenciar com: podman pod ps --filter name=$POD_NAME"
echo "   Logs: podman pod logs -f $POD_NAME"
echo "   Parar: podman pod stop $POD_NAME"