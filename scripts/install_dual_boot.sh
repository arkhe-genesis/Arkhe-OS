#!/bin/bash
# install_dual_boot.sh — Instala Arkhe OS em dual-boot com Windows/Linux
set -euo pipefail

echo "🔀 Instalando Arkhe OS em dual-boot..."
echo "⚠️  Certifique-se de ter feito backup dos seus dados."
read -p "Continuar? (s/N): " confirm
[[ "$confirm" != "s" ]] && exit 0

# 1. Redimensionar partição existente
echo "📏 Redimensionando partição principal..."
PART=$(lsblk -o NAME,SIZE,TYPE,MOUNTPOINT | grep part | grep "/" | awk '{print $1}')
sudo e2fsck -f /dev/$PART
sudo resize2fs /dev/$PART 50G  # Reduz para 50GB

# 2. Criar partição Arkhe (30GB)
echo "📦 Criando partição para Arkhe OS..."
sudo parted /dev/${PART%[0-9]*} mkpart primary ext4 50GB 80GB
sudo mkfs.ext4 /dev/${PART%[0-9]*}$((${PART##*[!0-9]}+1))

# 3. Instalar Arkhe OS na nova partição
echo "🧠 Instalando Arkhe OS..."
sudo mount /dev/${PART%[0-9]*}$((${PART##*[!0-9]}+1)) /mnt/arkhe
sudo rsync -a /cdrom/arkhe-rootfs/ /mnt/arkhe/
sudo arch-chroot /mnt/arkhe /usr/bin/arkhe-install --dual-boot

# 4. Configurar GRUB para dual-boot
echo "🔌 Configurando GRUB..."
cat << 'GRUB' | sudo tee -a /etc/grub.d/40_custom
menuentry "Arkhe OS v∞.Ω.∇+++.208.0" {
    set root=(hd0,gpt2)
    linux /boot/vmlinuz-arkhe root=/dev/sda2 quiet
    initrd /boot/initramfs-arkhe.img
}
GRUB
sudo update-grub

echo "✅ Dual-boot configurado! Reinicie e selecione Arkhe OS no GRUB."