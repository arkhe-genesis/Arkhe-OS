#!/bin/bash
set -e

WORK_DIR="/tmp/cathedral_live_build"
ISO_OUTPUT="cathedral-os-x86_64.iso"

echo "[1/4] Criando ambiente de build (debootstrap)..."
sudo debootstrap --arch=amd64 noble $WORK_DIR http://archive.ubuntu.com/ubuntu/

echo "[2/4] Copiando artefatos do Cathedral..."
sudo cp -r ../../core/target/release/cathedral-fast-core $WORK_DIR/opt/cathedral/bin/
sudo cp -r ../../core/target/release/cathedral-slow-brain $WORK_DIR/opt/cathedral/bin/
sudo cp systemd/*.service $WORK_DIR/etc/systemd/system/
sudo cp security/cathedral_fast.* $WORK_DIR/etc/selinux/

echo "[3/4] Compilando o LKM no ambiente isolado..."
sudo cp -r kernel/ $WORK_DIR/tmp/kernel_build/
sudo chroot $WORK_DIR /bin/bash -c "cd /tmp/kernel_build && make && make install"

echo "[4/4] Empacotando Imagem ISO (SquashFS)..."
sudo mksquashfs $WORK_DIR $WORK_DIR/iso/filesystem.squashfs -e boot
# (Aqui entra o grub-mkrescue para gerar o ISO final)
# grub-mkrescue -o $ISO_OUTPUT $WORK_DIR/iso

echo "Build concluído: $ISO_OUTPUT"
