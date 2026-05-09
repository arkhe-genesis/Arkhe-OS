#!/bin/bash
# scripts/bootstrap_pip_sovereign.sh — Setup do ambiente pip-sovereign
set -e

echo "🔐 Configurando pip-sovereign (Substrate 5018)..."

# 1. Verificar dependências do sistema
for cmd in python3 pip3 ipfs curl; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "❌ $cmd não encontrado. Instale antes de continuar."
        exit 1
    fi
done

# 2. Instalar pip-sovereign em modo desenvolvimento
echo "📦 Instalando pip-sovereign..."
cd "$(dirname "$0")/.."
pip3 install -e .

# 3. Configurar alias para substituir pip
if ! grep -q "alias pip=" ~/.bashrc 2>/dev/null; then
    echo "" >> ~/.bashrc
    echo "# ARKHE OS: pip-sovereign alias" >> ~/.bashrc
    echo "alias pip='pip-sovereign install'" >> ~/.bashrc
    echo "alias pip-sovereign='python3 -m pip_sovereign'" >> ~/.bashrc
    echo "✅ Aliases adicionados ao ~/.bashrc"
fi

# 4. Gerar chaves para assinatura de pacotes (opcional)
if [[ "${1:-}" == "--signing-keys" ]]; then
    echo "🔑 Gerando chaves para assinatura de pacotes..."
    mkdir -p ~/.arkhe/pip-sovereign/keys

    # Gerar par de chaves Falcon (simulado)
    if command -v falcon-keygen &> /dev/null; then
        falcon-keygen generate \
            --output ~/.arkhe/pip-sovereign/keys/maintainer \
            --password "${PIP_SIGNING_PASSWORD:-}"
        echo "✅ Chaves Falcon geradas"
    else
        echo "⚠️  falcon-keygen não encontrado — usando fallback"
        # Fallback: gerar chave Ed25519
        ssh-keygen -t ed25519 -f ~/.arkhe/pip-sovereign/keys/maintainer -N ""
    fi
fi

# 5. Configurar IPFS local (se necessário)
if ! ipfs id &> /dev/null; then
    echo "🌐 Inicializando IPFS local..."
    ipfs init
    ipfs config Addresses.API /ip4/127.0.0.1/tcp/5001
    ipfs config Addresses.Gateway /ip4/127.0.0.1/tcp/8080
    ipfs daemon --enable-gc &
    echo "⏳ Aguardando IPFS iniciar..."
    sleep 5
fi

# 6. Testar instalação
echo "🧪 Testando instalação soberana..."
pip-sovereign search "arkhe" --min-phi-rep 0.8 || echo "⚠️  Registry pode estar offline"

echo ""
echo "✅ pip-sovereign configurado!"
echo ""
echo "📋 Comandos úteis:"
echo "   pip-sovereign install requests==2.28.0    # Instalar com verificação"
echo "   pip-sovereign verify requests              # Verificar pacote instalado"
echo "   pip-sovereign coherence requirements.txt   # Analisar coerência"
echo "   pip-sovereign audit --environment          # Auditar ambiente"
echo ""
echo "🔄 Para usar como pip padrão, reinicie o shell ou execute:"
echo "   source ~/.bashrc"
echo ""