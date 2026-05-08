#!/bin/bash
# build.sh — Constrói o binário ARKHE AGI com PyInstaller

set -e

echo "🏛️  Iniciando build PyInstaller do ARKHE OS AGI Core..."

# Verificar dependências
if ! command -v pyinstaller &> /dev/null; then
    echo "❌ pyinstaller não encontrado. Instale com: pip install pyinstaller"
    exit 1
fi

# Limpar builds anteriores
rm -rf build/ dist/

# Criar diretório de hooks se necessário
mkdir -p hooks

# Executar PyInstaller
echo "🔨 Compilando com PyInstaller..."
pyinstaller \
    --onefile \
    --name arkhe-agi \
    --add-data "../config:agi/system32/config" \
    --add-data "../training:agi/system32/training" \
    --add-data "../federate/bootstrap/seeds.txt:agi/system32/federate/bootstrap" \
    --add-binary "../runtime/quantum/agi_rcp_bridge.so:." \
    --hidden-import torch \
    --hidden-import numpy \
    --hidden-import scipy \
    --hidden-import yaml \
    --hidden-import agi_transformer \
    --hidden-import coherence_reward \
    --hidden-import rcp_v2_engine \
    --hidden-import omni_core \
    --collect-all torch \
    --collect-all numpy \
    --collect-all scipy \
    --exclude-module tkinter \
    --exclude-module matplotlib \
    ../cli/main.py

# Verificar resultado
if [ -f dist/arkhe-agi ]; then
    echo "✅ Binário criado: dist/arkhe-agi"
    ls -lh dist/arkhe-agi
    file dist/arkhe-agi
else
    echo "❌ Falha na geração do binário"
    exit 1
fi

# Gerar checksum
sha256sum dist/arkhe-agi > dist/arkhe-agi.sha256
echo "📦 Checksum SHA256 gerado"

# Assinar com GPG (se chave disponível)
if [ -n "${AGI_GPG_KEY_ID}" ]; then
    gpg --detach-sign --armor --local-user "${AGI_GPG_KEY_ID}" dist/arkhe-agi
    echo "🔐 Binário assinado com GPG"
fi

echo "🎉 Build concluído com sucesso!"