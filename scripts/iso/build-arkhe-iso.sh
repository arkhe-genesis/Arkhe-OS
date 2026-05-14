#!/usr/bin/env bash
# ============================================================================
# ARKHE Ω‑TEMP — Build Script para ISO Bootável Bare Metal
# ============================================================================
set -euo pipefail

VERSION="7.0.0"
ARCH="${ARCH:-x86_64}"  # ou aarch64 para ARM
OUTPUT_DIR="./dist/arkhe-os-${VERSION}-${ARCH}"
ISO_NAME="arkhe-os-${VERSION}-${ARCH}.iso"

echo "🏗️  Construindo ArkheOS ISO v${VERSION} para ${ARCH}..."

# 1. Preparar ambiente de build
mkdir -p "${OUTPUT_DIR}"
cd "${OUTPUT_DIR}"

# 2. Baixar base minimal (Alpine Linux para tamanho reduzido)
echo "📦 Baixando base Alpine Linux..."
wget -q https://dl-cdn.alpinelinux.org/alpine/v3.19/releases/${ARCH}/alpine-virt-${ARCH}-${VERSION}.tar.gz
tar -xzf alpine-virt-*.tar.gz --strip-components=1

# 3. Instalar Arkhe Runtime
echo "🧠 Instalando Arkhe Runtime..."
curl -sL https://arkhe.io/runtime/install.sh | bash -s -- --prefix=/usr/local/arkhe

# 4. Copiar microkernel WASM/WASI
echo "⚙️  Configurando microkernel WASM/WASI..."
mkdir -p boot/kernel
cp /usr/local/arkhe/bin/arkhe-microkernel.wasm boot/kernel/
cp /usr/local/arkhe/bin/wasi-libc.wasm boot/kernel/

# 5. Configurar bootloader (GRUB com suporte a WASM)
echo "🔌 Configurando GRUB com suporte WASM..."
mkdir -p boot/grub
cat > boot/grub/grub.cfg << 'EOF'
set timeout=5
set default=0

menuentry "ArkheOS v7.0.0 (Bare Metal)" {
    linux /boot/vmlinuz root=/dev/sda1 quiet splash
    initrd /boot/initramfs.img
    wasm /boot/kernel/arkhe-microkernel.wasm
    wasm /boot/kernel/wasi-libc.wasm
}

menuentry "ArkheOS (Recovery Mode)" {
    linux /boot/vmlinuz root=/dev/sda1 single
    initrd /boot/initramfs.img
}
EOF

# 6. Criar initramfs com Arkhe Runtime
echo "📦 Criando initramfs..."
mkdir -p initramfs/{bin,lib,etc,proc,sys,dev,run}
cp /usr/local/arkhe/bin/arkh initramfs/bin/
cp /usr/local/arkhe/lib/*.so initramfs/lib/ 2>/dev/null || true

# Script de init mínimo
cat > initramfs/init << 'EOF'
#!/bin/sh
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t devtmpfs devtmpfs /dev

# Iniciar Arkhe Runtime
exec /bin/arkh --daemon --bare-metal

# Fallback para shell se falhar
exec /bin/sh
EOF
chmod +x initramfs/init

# Compactar initramfs
cd initramfs
find . | cpio -o -H newc | gzip > ../boot/initramfs.img
cd ..

# 7. Copiar kernel Linux (para compatibilidade de drivers)
echo "🐧 Copiando kernel Linux para compatibilidade..."
cp /boot/vmlinuz-* boot/vmlinuz 2>/dev/null || echo "⚠️ Kernel não encontrado; usando kernel genérico"

# 8. Gerar ISO com xorriso
echo "💿 Gerando imagem ISO..."
xorriso -as mkisofs \
    -V "ARKHE_OS_${VERSION}" \
    -J -R -VOLID "ARKHE_OS" \
    -b boot/grub/eltorito.img \
    -no-emul-boot -boot-load-size 4 -boot-info-table \
    -c boot/grub/boot.catalog \
    -o "${ISO_NAME}" \
    boot/

# 9. Assinar ISO com chave da Catedral
echo "🔐 Assinando ISO com chave da Catedral..."
openssl dgst -sha3-256 -sign /etc/arkhe/keys/cathedral-private.pem -out "${ISO_NAME}.sig" "${ISO_NAME}"

# 10. Gerar checksums e metadados
echo "📋 Gerando metadados de release..."
cat > "${ISO_NAME}.meta.json" << EOF
{
  "version": "${VERSION}",
  "architecture": "${ARCH}",
  "build_timestamp": $(date +%s),
  "iso_sha3_256": "$(sha3sum ${ISO_NAME} | cut -d' ' -f1)",
  "signature": "$(base64 ${ISO_NAME}.sig | tr -d '\n')",
  "min_ram_gb": 4,
  "min_disk_gb": 20,
  "supported_hardware": ["x86_64", "aarch64"],
  "features": ["bare-metal", "wasm-kernel", "arkfs", "wheeler-mesh"]
}
EOF

echo "✅ ArkheOS ISO construída com sucesso!"
echo "📦 Arquivo: ${ISO_NAME}"
echo "🔐 Assinatura: ${ISO_NAME}.sig"
echo "📋 Metadados: ${ISO_NAME}.meta.json"
echo ""
echo "🚀 Para instalar:"
echo "   1. Grave a ISO em um USB: dd if=${ISO_NAME} of=/dev/sdX bs=4M status=progress"
echo "   2. Inicie a máquina a partir do USB"
echo "   3. Siga o assistente de instalação interativo"