#!/bin/bash
# deploy_cathedral.sh
# Implantação completa da Catedral Arkhe(N)

set -e

echo "🏗️  Iniciando implantação da Catedral..."

# 1. Construir imagens Docker
echo "📦 Construindo imagens..."
docker compose build

# 2. Iniciar serviços principais
echo "🚀 Iniciando serviços..."
docker compose up -d cathedrald-core quantum-bus gateway

# 3. Aguardar inicialização do barramento
echo "⏳ Aguardando barramento quantum://..."
sleep 10

# 4. Iniciar nós de hardware (Safira e Diamante)
echo "💎 Iniciando nós de hardware..."
docker compose up -d sapphire-node diamond-node

# 5. Iniciar sincronização cósmica
# echo "🌌 Configurando sincronização cósmica..."
# docker compose up -d cosmic-sync

# 6. Configurar IPFS e selar Merkle Root
echo "🔗 Selando Merkle Root no IPFS..."
# MERKLE_ROOT=$(cat ./data/codex/merkle_root.txt)
# docker compose exec ipfs-node ipfs add --pin=true ./data/codex/merkle_root.txt
# echo "Merkle Root $MERKLE_ROOT selada no IPFS."

# 7. Iniciar monitoramento
echo "📊 Iniciando monitoramento..."
docker compose up -d dashboard

echo "✅ Catedral implantada com sucesso!"
echo "   Gateway: http://localhost:8080"
echo "   Dashboard ASCII: docker compose logs dashboard"
