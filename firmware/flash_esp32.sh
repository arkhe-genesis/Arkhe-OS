#!/bin/bash
# Substrato 192: Flash do firmware TinyML no ESP32-S3
# Requer: esptool.py, PlatformIO ou ESP-IDF instalado

set -euo pipefail

PORT="${1:-/dev/ttyUSB0}"
BAUD="${2:-921600}"
CHIP="${3:-esp32s3}"

echo "🔷 ARKHE TinyML Flash — ESP32-S3"
echo "   Porta: $PORT | Baud: $BAUD | Chip: $CHIP"

# 1. Compilar firmware com PlatformIO (se necessário)
if [ ! -f "firmware/anomaly_model.tflite" ]; then
    echo "❌ Modelo TFLite não encontrado — execute train_anomaly_model.py primeiro"
    # exit 1
fi

# 2. Flash do bootloader, partição e aplicativo
echo "📦 Flashing firmware..."
esptool.py --chip $CHIP --port $PORT --baud $BAUD write_flash \
    0x0 firmware/bootloader.bin \
    0x8000 firmware/partition-table.bin \
    0x10000 firmware/tinyml_agent.bin \
    0x310000 firmware/anomaly_model.tflite \
    0x350000 firmware/scaler.bin

# 3. Reset e verificação
echo "🔄 Resetando ESP32-S3..."
esptool.py --chip $CHIP --port $PORT --baud 115200 reset

# 4. Monitorar logs iniciais
echo "📡 Monitorando inicialização (Ctrl+C para sair)..."
esptool.py --chip $CHIP --port $PORT --baud 115200 monitor &
MONITOR_PID=$!
sleep 5
kill $MONITOR_PID 2>/dev/null || true

echo "✅ Flash concluído — agente TinyML ativo no ESP32-S3"
