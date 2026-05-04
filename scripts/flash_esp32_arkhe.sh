#!/bin/bash
# =============================================================================
# flash_esp32_arkhe.sh — Ritual de Flashing para Nó Sensorial do Casulo
# =============================================================================
# Ferreiro Directive: "CADA EFUSE QUEIMADO É UMA FRATURA IRREVERSÍVEL."
# =============================================================================

set -e

# =============================================================================
# CONFIGURAÇÃO RITUAL
# =============================================================================
DEVICE_PORT="/dev/ttyUSB0"
BAUD_RATE="460800"
BOOTLOADER="bootloader/bootloader.bin"
PARTITION_TABLE="partitions.csv"
FIRMWARE="build/arkhe_esp32_sensor.bin"
SECURE_BOOT_KEY="keys/secure_boot_signing_key.pem"
FLASH_ENCRYPTION_KEY="keys/flash_encryption_key.bin"

# Modo Simulação (Padrão: true para segurança no sandbox)
SIMULATE=true

# Opções de segurança
ENABLE_SECURE_BOOT=true
ENABLE_FLASH_ENCRYPTION=true
BURN_EFUSES=true
DISABLE_JTAG=true

# =============================================================================
# WRAPPER DE EXECUÇÃO
# =============================================================================
run_cmd() {
    if [ "$SIMULATE" = true ]; then
        echo "[SIMULAÇÃO] $*"
    else
        "$@"
    fi
}

echo "┌─────────────────────────────────────────────────────────────┐"
echo "│  RITUAL DE FLASHING — NÓ SENSORIAL DO CASULO               │"
echo "└─────────────────────────────────────────────────────────────┘"

read -p "Digite 'EU SEI O QUE ESTOU FAZENDO' para continuar: " confirmation
if [ "$confirmation" != "EU SEI O QUE ESTOU FAZENDO" ]; then
    echo "Ritual abortado."
    exit 0
fi

# 1. Verificação de Assinatura
echo "--- FASE 1: VERIFICAÇÃO DE ASSINATURA ---"
run_cmd espsecure.py verify_signature --version 2 --keyfile "$SECURE_BOOT_KEY" "$FIRMWARE"

# 2. Gravação Inicial
echo "--- FASE 2: GRAVAÇÃO INICIAL ---"
run_cmd esptool.py --chip esp32 --port "$DEVICE_PORT" erase_flash
run_cmd esptool.py --chip esp32 --port "$DEVICE_PORT" --baud "$BAUD_RATE" write_flash 0x1000 "$BOOTLOADER"
run_cmd esptool.py --chip esp32 --port "$DEVICE_PORT" --baud "$BAUD_RATE" write_flash 0x8000 "$PARTITION_TABLE"
run_cmd esptool.py --chip esp32 --port "$DEVICE_PORT" --baud "$BAUD_RATE" write_flash 0x20000 "$FIRMWARE"

# 3. eFuses
if [ "$BURN_EFUSES" = true ]; then
    echo "--- FASE 3: QUEIMA DE EFUSES (IRREVERSÍVEL) ---"
    read -p "CONFIRMA QUEIMA DE EFUSES? (S/N): " burn_confirm
    if [ "$burn_confirm" = "S" ]; then
        run_cmd espefuse.py --port "$DEVICE_PORT" burn_key flash_encryption "$FLASH_ENCRYPTION_KEY"
        run_cmd espefuse.py --port "$DEVICE_PORT" --do-not-confirm burn_efuse FLASH_CRYPT_CNT
        run_cmd espefuse.py --port "$DEVICE_PORT" burn_key secure_boot_v2 <(openssl ec -in "$SECURE_BOOT_KEY" -pubout -outform DER 2>/dev/null)
        run_cmd espefuse.py --port "$DEVICE_PORT" --do-not-confirm burn_efuse SECURE_BOOT_EN
        [ "$DISABLE_JTAG" = true ] && run_cmd espefuse.py --port "$DEVICE_PORT" --do-not-confirm burn_efuse JTAG_DISABLE
    fi
fi

echo "Ritual concluído."
