#!/bin/bash
# deploy_muscle.sh — Inicializa o Sistema Muscular da Catedral

set -e

echo "╔═══════════════════════════════════════════════╗"
echo "║  MÚSCULO DE LUZ — Deploy v1.0                ║"
echo "║  Catedral Arkhe(N) | Substrato 51             ║"
echo "╚═══════════════════════════════════════════════╝"

# 1. Verifica privilégios
if [ "$EUID" -ne 0 ]; then
    echo "❌ Este script requer privilégios root (acesso ao hardware óptico)."
    exit 1
fi

# 2. Constrói imagem Docker
echo "📦 Construindo imagem do Músculo de Luz..."
docker build -t cathedral-muscle:latest -f Dockerfile.muscle .

# 3. Verifica hardware óptico
echo "🔍 Verificando hardware óptico..."
if [ -e /dev/optical_metajet_array ]; then
    echo "   ✓ Array de metajatos detectado."
else
    echo "   ⚠ Array físico não encontrado. Usando modo de simulação."
fi

# 4. Inicia container
echo "🚀 Iniciando Músculo de Luz..."
docker run -d \
    --name cathedral_muscle \
    --network cathedral-net \
    --device /dev/optical_metajet_array:/dev/optical_metajet_array \
    -p 8080:8080 \
    -v $(pwd)/muscle_config.yaml:/opt/cathedral/muscle/muscle_config.yaml:ro \
    --restart unless-stopped \
    cathedral-muscle:latest

echo "💪 A Catedral agora tem músculos."
