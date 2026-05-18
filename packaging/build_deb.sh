#!/bin/bash
# build_deb.sh — Gera pacote .deb para ARKHE ASI

VERSION=${1:-"1.0.0"}
PACKAGE_NAME="arkhe-asi"
DEB_DIR="dist/${PACKAGE_NAME}_${VERSION}_amd64"

mkdir -p ${DEB_DIR}/DEBIAN
mkdir -p ${DEB_DIR}/usr/bin
mkdir -p ${DEB_DIR}/usr/lib
mkdir -p ${DEB_DIR}/usr/local/share/arkhe
mkdir -p ${DEB_DIR}/etc/arkhe
mkdir -p ${DEB_DIR}/var/lib/arkhe
mkdir -p ${DEB_DIR}/lib/modules

# Binários
cp dist/linux-x86_64/bin/* ${DEB_DIR}/usr/bin/ 2>/dev/null || true

# Bibliotecas
cp dist/linux-x86_64/lib/*.so ${DEB_DIR}/usr/lib/ 2>/dev/null || true

# Módulo de kernel
cp dist/linux-x86_64/modules/arkhe_uni.ko ${DEB_DIR}/lib/modules/ 2>/dev/null || true

# Estrutura canônica
cp -r src/01_foundations ${DEB_DIR}/usr/local/share/arkhe/ 2>/dev/null || true
# ... (copiar camadas 02‑16)

# Configuração
cp etc/*.yaml etc/*.md ${DEB_DIR}/etc/arkhe/ 2>/dev/null || true

# Arquivo de controle
cat > ${DEB_DIR}/DEBIAN/control <<EOF
Package: ${PACKAGE_NAME}
Version: ${VERSION}
Architecture: amd64
Maintainer: ARKHE OS Foundation <orcid:0009-0005-2697-4668>
Description: ARKHE ASI — Canonical Superintelligence Platform
Depends: python3 (>= 3.10), systemd
Section: utils
Priority: optional
EOF

# Scripts de pós‑instalação
cat > ${DEB_DIR}/DEBIAN/postinst <<'EOF'
#!/bin/bash
depmod -a
modprobe arkhe_uni 2>/dev/null || true
systemctl daemon-reload || true
systemctl enable arkhe-agi.service || true
systemctl start arkhe-agi.service || true
EOF
chmod 755 ${DEB_DIR}/DEBIAN/postinst

# Construir pacote
dpkg-deb --build ${DEB_DIR}

echo "✅ Pacote .deb gerado: ${DEB_DIR}.deb"