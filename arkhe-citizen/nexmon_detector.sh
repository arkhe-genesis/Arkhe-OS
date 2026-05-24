#!/system/bin/sh
# ARKHE OS — Substrato 409-NEXMON-CSI
# Script de deteção automática de chip Broadcom/Cypress para Nexmon
# Arquiteto: Rafael Oliveira (ORCID: 0009-0005-2697-4668)

set -e

TAG="ArkheNexmon"
NEXMON_DB="/data/local/tmp/nexmon_chip_db.json"

log() {
    log -p i -t "$TAG" "$1"
    echo "[$TAG] $1"
}

# ─── 1. DETETAR CHIP WIFI ───
log "A detetar chipset WiFi..."

CHIP_INFO=""
CHIP_FAMILY=""
CHIP_REVISION=""

# Método 1: via /proc/cpuinfo e wifi driver
if [ -f /sys/class/net/wlan0/device/uevent ]; then
    CHIP_INFO=$(cat /sys/class/net/wlan0/device/uevent | grep "DRIVER" | cut -d= -f2)
    log "Driver detectado: $CHIP_INFO"
fi

# Método 2: via dmesg
if [ -z "$CHIP_INFO" ]; then
    CHIP_INFO=$(dmesg | grep -i "brcm\|broadcom\|bcmdhd" | tail -1 | grep -o "bcmdhd[0-9]*\|brcm[0-9]*" | head -1)
    if [ -n "$CHIP_INFO" ]; then
        log "Chip detectado via dmesg: $CHIP_INFO"
    fi
fi

# Método 3: via propriedades do sistema
if [ -z "$CHIP_INFO" ]; then
    CHIP_INFO=$(getprop wifi.interface.driver.name)
    if [ -n "$CHIP_INFO" ]; then
        log "Chip detectado via propriedade: $CHIP_INFO"
    fi
fi

# ─── 2. IDENTIFICAR FAMÍLIA DO CHIP ───

identify_chip_family() {
    local chip="$1"

    case "$chip" in
        *"43430"*|*"43436"*|*"43438"*)
            CHIP_FAMILY="bcm43430a1"
            CHIP_REVISION="1"
            ;;
        *"43455"*)
            CHIP_FAMILY="bcm43455c0"
            CHIP_REVISION="0"
            ;;
        *"4358"*)
            CHIP_FAMILY="bcm4358"
            CHIP_REVISION="0"
            ;;
        *"43596"*)
            CHIP_FAMILY="bcm43596a0"
            CHIP_REVISION="0"
            ;;
        *"4375"*)
            CHIP_FAMILY="bcm4375b1"
            CHIP_REVISION="1"
            ;;
        *"4366"*)
            CHIP_FAMILY="bcm4366c0"
            CHIP_REVISION="0"
            ;;
        *"4339"*)
            CHIP_FAMILY="bcm4339"
            CHIP_REVISION="0"
            ;;
        *"4335"*)
            CHIP_FAMILY="bcm4335b0"
            CHIP_REVISION="0"
            ;;
        *)
            CHIP_FAMILY="unknown"
            CHIP_REVISION="unknown"
            ;;
    esac

    log "Família identificada: $CHIP_FAMILY (rev $CHIP_REVISION)"
}

identify_chip_family "$CHIP_INFO"

# ─── 3. VERIFICAR SUPORTE NEXMON ───

log "A verificar suporte Nexmon para $CHIP_FAMILY..."

# Base de dados de chips suportados (simplificada)
SUPPORTED_CHIPS="bcm4339 bcm43430a1 bcm43455c0 bcm4358 bcm43596a0 bcm4366c0 bcm4335b0"

if echo "$SUPPORTED_CHIPS" | grep -q "$CHIP_FAMILY"; then
    log "✅ Chip SUPORTADO pelo Nexmon"

    # Verificar se já está patcheado
    if [ -f /dev/nexmon_csi ]; then
        log "✅ Nexmon já ativo (/dev/nexmon_csi existe)"
        echo '{"status":"active","chip":"'$CHIP_FAMILY'","patched":true}' > /data/local/tmp/nexmon_status.json
        exit 0
    fi

    # Verificar se nexutil existe
    if command -v nexutil >/dev/null 2>&1; then
        log "✅ nexutil encontrado"
    else
        log "⚠️ nexutil não encontrado — módulo Magisk necessário"
        echo '{"status":"needs_magisk","chip":"'$CHIP_FAMILY'","patched":false}' > /data/local/tmp/nexmon_status.json
        exit 1
    fi

    echo '{"status":"supported","chip":"'$CHIP_FAMILY'","patched":false}' > /data/local/tmp/nexmon_status.json

else
    log "❌ Chip NÃO suportado pelo Nexmon: $CHIP_FAMILY"
    echo '{"status":"unsupported","chip":"'$CHIP_FAMILY'","patched":false}' > /data/local/tmp/nexmon_status.json
    exit 1
fi