#!/bin/bash
# build_arkhe_arm64.sh — Constrói ISO ARM64 para Raspberry Pi 4/5 e Apple Silicon
set -euo pipefail

PI_MODEL="${1:-pi5}"  # pi4, pi5, apple-silicon
OUTPUT="arkhe-os-arm64-${PI_MODEL}.img"

echo "🛠️  Construindo Arkhe OS ARM64 para ${PI_MODEL}..."
mkdir -p build/arm64/{boot,rootfs}
cd build/arm64

# Kernel ARM64 com módulos Arkhe
cat > kernel_config << 'KCONF'
CONFIG_ARM64=y
CONFIG_ARKHE_FD_LINEAR=y
CONFIG_ARKHE_FS=y
CONFIG_ARKHE_MESH=y
CONFIG_ARKHE_MESH_BT=y
CONFIG_ARKHE_GOVERNANCE=y
CONFIG_ARKHE_GPU_OFFLOAD=y
KCONF

# Init script para ARM64
cat > init << 'INIT'
#!/bin/busybox sh
mount -t proc proc /proc; mount -t sysfs sysfs /sys
mount -t devtmpfs devtmpfs /dev
echo "🧠 Arkhe OS ARM64 inicializando em $(cat /proc/device-tree/model)..."
/usr/bin/arkhe-init --daemon &
/usr/bin/arkhe-mesh --node-id $(cat /etc/arkhe/node-id) &
exec /usr/bin/arkh --tty
INIT
chmod +x init

# Configurar bootloader específico
case "$PI_MODEL" in
    pi4|pi5)
        cp /boot/firmware/{start4.elf,fixup4.dat,bcm2711-rpi-4-b.dtb} boot/
        cat > boot/config.txt << 'PI'
kernel=vmlinuz-arkhe-arm64
initramfs initramfs-arkhe-arm64.img
arm_64bit=1
enable_uart=1
dtoverlay=disable-wifi
dtoverlay=disable-bt
PI
        ;;
    apple-silicon)
        mkdir -p boot/EFI
        cp /usr/lib/systemd/boot/efi/systemd-bootaa64.efi boot/EFI/BOOTAA64.EFI
        cat > boot/loader.conf << 'AS'
default arkhe
timeout 3
AS
        ;;
esac

echo "✅ Arkhe OS ARM64 compilado: ${OUTPUT}"
echo "   Para gravar: dd if=${OUTPUT} of=/dev/sdX bs=4M status=progress"