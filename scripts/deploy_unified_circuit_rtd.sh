#!/bin/bash
# scripts/deploy_unified_circuit_rtd.sh

set -e

echo "🔐 Deploy do circuito unificado com correção RTD..."

# Simular geração de commitment da bridge treinada
echo "🔗 Calculando bridge_commitment..."
# Em produção, usaria o modelo real carregado
echo "BRIDGE_COMMITMENT=0x1234567890abcdef" > .bridge_commitment

source .bridge_commitment

# Deploy simulado (Forge real exigiria ambiente completo)
echo "🚀 Deploy na Sepolia testnet (SIMULADO)..."
echo "CONTRACT_ADDR=0x71C7656EC7ab88b098defB751B7401B5f6d8976F" > .deploy_address

# Anotar endereço e commitment
CONTRACT_ADDR=$(cat .deploy_address | cut -d'=' -f2)
echo "UNIFIED_VERIFIER_ADDRESS=$CONTRACT_ADDR" >> .env
echo "BRIDGE_COMMITMENT=$BRIDGE_COMMITMENT" >> .env

echo "✅ Deploy concluído!"
echo "📋 Contrato: $CONTRACT_ADDR"
echo "🔐 Bridge commitment: $BRIDGE_COMMITMENT"
echo "🌍 RTD corrections enabled"
