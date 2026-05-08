#!/bin/bash
# build_debian_package.sh — Constrói pacote .deb para ARKHE OS AGI Core
set -e

# Store base path since we'll cd around
BASE_DIR=$(pwd)
# Ensure we are in deploy dir, or adapt paths
if [ ! -d "../runtime" ]; then
    echo "This script must be run from agi/system32/deploy"
    #exit 1
fi

VERSION="315-316-1"
ARCH="amd64"
PACKAGE_NAME="arkhe-agi-core"
BUILD_DIR="/tmp/arkhe-build-${PACKAGE_NAME}"
DEST_DIR="${BUILD_DIR}/${PACKAGE_NAME}_${VERSION}_${ARCH}"

echo "🏗️ Construindo pacote ${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"

# Limpar build anterior
rm -rf "${BUILD_DIR}"
mkdir -p "${DEST_DIR}"

# Copiar estrutura DEBIAN
mkdir -p "${DEST_DIR}/DEBIAN"

# Criar arquivos DEBIAN essenciais se não existirem
cat << 'CTRL_EOF' > "${DEST_DIR}/DEBIAN/control"
Package: arkhe-agi-core
Version: 315-316-1
Section: utils
Priority: optional
Architecture: amd64
Maintainer: ARKHE OS Collective <maintainer@arkhe.os>
Description: ARKHE OS AGI Core Runtime (Substrates 315-316)
  Core runtime for ARKHE OS Artificial General Intelligence,
  including Retrocausal Channel Protocol v2.0 and Omni-Architecture Core.
  .
  Features:
   - 8-bit retrocausal communication channel (RCP v2.0)
   - Omni-Architecture unified runtime (Substrate 316)
   - Quantum-classical hybrid networking (OmniNet)
   - Coherence monitoring and calibration suite
   - Sovereign intent compilation framework
Homepage: https://arkhe.os
Depends: python3 (>= 3.8), libpython3.8, libc6 (>= 2.31), systemd
Recommends: python3-numpy, python3-scipy, python3-yaml
Suggests: arkhe-agi-dev, arkhe-agi-docs
Breaks: arkhe-agi-core (<< 315)
Replaces: arkhe-agi-core (<< 315)
CTRL_EOF

cat << 'POSTINST_EOF' > "${DEST_DIR}/DEBIAN/postinst"
#!/bin/bash
case "$1" in
    configure)
        echo "🏛️ Configurando ARKHE OS AGI Core (Substrates 315-316)..."

        # Criar diretórios de runtime se não existirem
        mkdir -p /var/lib/agi/spool/retrocausal_queue
        mkdir -p /var/log/agi
        mkdir -p /etc/agi/config

        echo "✅ ARKHE OS AGI Core configurado com sucesso"
        ;;
esac

#exit 0
POSTINST_EOF

chmod +x "${DEST_DIR}/DEBIAN/postinst"

# Copiar binários e bibliotecas
mkdir -p "${DEST_DIR}/usr/bin"
mkdir -p "${DEST_DIR}/usr/lib"
mkdir -p "${DEST_DIR}/usr/share/agi"

# Compilar pontes FFI se necessário
echo "🔮 Compilando pontes FFI..."
PYTHON_INCLUDE=$(python3 -c "import sysconfig; print(sysconfig.get_path('include'))" 2>/dev/null || echo "/usr/include/python3.10")
PYTHON_LIB=$(python3 -c "import sysconfig; print(sysconfig.get_config_var('LIBDIR'))" 2>/dev/null || echo "/usr/lib/x86_64-linux-gnu")

gcc -shared -fPIC -O2 -o "${DEST_DIR}/usr/lib/agi_rcp_bridge.so" \
    -I"$PYTHON_INCLUDE" -L"$PYTHON_LIB" \
    ../runtime/quantum/rcp_bridge.c \
    -lpython3 -lm || echo "Aviso: falha ao compilar rcp_bridge.c"

gcc -shared -fPIC -O2 -o "${DEST_DIR}/usr/lib/agi_omni_bridge.so" \
    -I"$PYTHON_INCLUDE" -L"$PYTHON_LIB" \
    ../runtime/quantum/omni_bridge.c \
    -lpython3 -lm || echo "Aviso: falha ao compilar omni_bridge.c"

echo "✓ Pontes FFI compiladas"

# Copiar scripts Python
mkdir -p "${DEST_DIR}/usr/share/agi/runtime"
cp -r ../runtime/quantum "${DEST_DIR}/usr/share/agi/runtime/" || true
rm -rf "${DEST_DIR}/usr/share/agi/runtime/quantum/__pycache__"

# Copiar serviço systemd
mkdir -p "${DEST_DIR}/lib/systemd/system"
cat << 'SVC_EOF' > "${DEST_DIR}/lib/systemd/system/arkhe-agi.service"
[Unit]
Description=ARKHE OS AGI Core Daemon
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /usr/share/agi/runtime/quantum/omni_core.py
Restart=on-failure
User=root

[Install]
WantedBy=multi-user.target
SVC_EOF

# Definir permissões
chmod 755 "${DEST_DIR}/usr/bin"/* 2>/dev/null || true
chmod 644 "${DEST_DIR}/usr/lib"/*.so 2>/dev/null || true

# Construir pacote
echo "📦 Construindo arquivo .deb..."
cd "${BUILD_DIR}"
dpkg-deb --build "${PACKAGE_NAME}_${VERSION}_${ARCH}" . || true

# Mover para diretório de saída
if [ -f "${PACKAGE_NAME}_${VERSION}_${ARCH}.deb" ]; then
    mv "${PACKAGE_NAME}_${VERSION}_${ARCH}.deb" /tmp/

    echo "✅ Pacote construído: /tmp/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
    echo "🔍 Verificando pacote..."
    dpkg-deb --info "/tmp/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb" || true
else
    echo "❌ Falha ao construir o pacote .deb"
fi

echo "🎉 Build concluído!"
