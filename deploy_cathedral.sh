#!/bin/bash
# deploy_cathedral.sh
# Implantação completa da Catedral Arkhe(N)

set -e

echo "🏗️  Iniciando implantação da Catedral..."

# 1. Construir imagens Docker
echo "📦 Construindo imagens..."
docker compose build

# 2. Iniciar o Guardião do Nome (numa)
echo "🛡️  Iniciando Guardião do Nome (numa)..."
docker compose up -d numa
sleep 5 # Aguarda o DNS estabilizar

# 3. Iniciar serviços principais
echo "🚀 Iniciando serviços principais..."
docker compose up -d cathedrald-core quantum-bus gateway

# 4. Aguardar inicialização do barramento
echo "⏳ Aguardando barramento quantum://..."
sleep 10

# 5. Iniciar nós de hardware (Safira e Diamante)
echo "💎 Iniciando nós de hardware..."
docker compose up -d sapphire-node diamond-node

# 6. Configurar IPFS e selar Merkle Root
echo "🔗 Selando Merkle Root no IPFS..."
# MERKLE_ROOT=$(cat ./data/codex/merkle_root.txt)
# docker compose exec ipfs-node ipfs add --pin=true ./data/codex/merkle_root.txt
# echo "Merkle Root $MERKLE_ROOT selada no IPFS."

# 7. Iniciar monitoramento
echo "📊 Iniciando monitoramento..."
docker compose up -d entropy-monitor

echo "✅ Catedral implantada com sucesso!"
echo "   Gateway: http://localhost:8080"
echo "   DNS Dashboard: http://localhost:5380"
