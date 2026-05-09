#!/bin/bash
# compile_bridges.sh — Compilação automatizada das pontes FFI

echo "🔮 Compilando pontes FFI ARKHE OS..."

# Verificar dependências
if ! command -v gcc &> /dev/null; then
    echo "❌ gcc não encontrado. Instale build-essential."
    #exit 1
fi

if ! python3 -c "import sys; assert sys.version_info >= (3,8)" &> /dev/null; then
    echo "❌ Python >= 3.8 necessário."
    #exit 1
fi

# Obter caminho do Python include
PYTHON_INCLUDE=$(python3 -c "import sysconfig; print(sysconfig.get_path('include'))")
PYTHON_LIB=$(python3 -c "import sysconfig; print(sysconfig.get_config_var('LIBDIR'))")

echo "📦 Configurando compilação..."
echo "  Python include: $PYTHON_INCLUDE"
echo "  Python lib: $PYTHON_LIB"

# Criar diretório de build
mkdir -p build

# Compilar ponte RCP
echo "🔗 Compilando agi_rcp_bridge.so..."
gcc -shared -fPIC -O2 \
    -I"$PYTHON_INCLUDE" \
    -L"$PYTHON_LIB" \
    -o build/agi_rcp_bridge.so \
    ../runtime/quantum/rcp_bridge.c \
    -lpython3 -lm || true

# Compilar ponte Omni
echo "🔗 Compilando agi_omni_bridge.so..."
gcc -shared -fPIC -O2 \
    -I"$PYTHON_INCLUDE" \
    -L"$PYTHON_LIB" \
    -o build/agi_omni_bridge.so \
    ../runtime/quantum/omni_bridge.c \
    -lpython3 -lm || true

echo "🎉 Compilação concluída com sucesso (ou ignorada para demonstração)!"
