#!/bin/bash
# install_cathedral.sh — ARKHE OS Kernel Module Installation
# Substrate: 212-KM
# Canonical Seal: bfbc03900123006c35442cf12f2d0189b0496856d8eb3e23fbbbbe4e46cbf31e

set -e

MODULE_NAME="arkhe_cobol_parser"
DEVICE_NAME="arkhe_cobol"
CLASS_NAME="arkhe"
ORCID="0009-0005-2697-4668"

echo "🏛️ ARKHE OS — Kernel Module Installation"
echo "   Substrate: 212-KM"
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

# Criar device node (se não criado automaticamente)
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
sudo dmesg | grep "ARKHE:" | tail -10

echo ""
echo "🎯 Installation complete!"
echo "   Module: $MODULE_NAME"
echo "   Device: /dev/$DEVICE_NAME"
echo "   Class: /sys/class/$CLASS_NAME/"
echo ""
echo "📊 Next steps:"
echo "   1. Test with: ./test_kernel_parser"
echo "   2. Unload with: sudo rmmod $MODULE_NAME"
echo "   3. Check status: make status"
