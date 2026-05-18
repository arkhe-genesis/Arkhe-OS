#!/bin/bash
# install_unikernel.sh — ARKHE Uni‑Kernel Polyglot Installation
# Substrate: 216-KM

set -e

MODULE_NAME="arkhe_unikernel_polyglot"
DEVICE_NAME="arkhe_uni"
CLASS_NAME="arkhe"
ORCID="0009-0005-2697-4668"

echo "🏛️ ARKHE OS — Uni‑Kernel Polyglot Installation"
echo "   Substrate: 216-KM"
echo "   Architect: $ORCID"
echo ""

# Verificar kernel version
KERNEL_VERSION=$(uname -r)
echo "📋 Kernel version: $KERNEL_VERSION"

if [[ ! -d "/lib/modules/$KERNEL_VERSION/build" ]]; then
    echo "❌ Kernel headers not found. Install with:"
    echo "   sudo apt-get install linux-headers-$KERNEL_VERSION"
    exit 1
fi

# Compilar módulo
echo "🔨 Compiling kernel module..."
make -C /lib/modules/$KERNEL_VERSION/build M=$(pwd) modules

# Verificar módulo compilado
if [[ ! -f "$MODULE_NAME.ko" ]]; then
    echo "❌ Module compilation failed"
    exit 1
fi

echo "✅ Module compiled: $MODULE_NAME.ko"

# Carregar módulo
echo "📥 Loading kernel module..."
sudo insmod $MODULE_NAME.ko

# Verificar carregamento
sleep 1
if ! lsmod | grep -q "$MODULE_NAME"; then
    echo "❌ Module failed to load"
    exit 1
fi

echo "✅ Module loaded successfully"

# Criar device node
MAJOR=$(grep "$DEVICE_NAME" /proc/devices | awk '{print $1}')
if [[ -n "$MAJOR" ]]; then
    echo "📟 Device major number: $MAJOR"
    sudo mknod /dev/$DEVICE_NAME c $MAJOR 0 2>/dev/null || true
    sudo chmod 666 /dev/$DEVICE_NAME
    echo "✅ Device node: /dev/$DEVICE_NAME"
fi

# Verificar logs
echo ""
echo "📜 Kernel log:"
sudo dmesg | grep "ARKHE_UNI:" | tail -10

echo ""
echo "🎯 Installation complete!"
echo "   Module: $MODULE_NAME"
echo "   Device: /dev/$DEVICE_NAME"
echo "   Class: /sys/class/$CLASS_NAME/"
echo ""
echo "📊 Next steps:"
echo "   1. Test with: ./test_unikernel_polyglot"
echo "   2. Register languages: ioctl ARKHE_IOCTL_REGISTER_LANGUAGE"
echo "   3. Parse code: ioctl ARKHE_IOCTL_PARSE_LANG"
