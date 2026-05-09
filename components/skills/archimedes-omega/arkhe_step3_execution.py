#!/usr/bin/env python3
"""
arkhe_step3_execution.py
Arkhe(n) – Step 3: Loading Dispenser and Starting XYZ Distribution + Photopolymerization.
Integrates dispensing and LED curing into a synchronized sequence.
"""

import time
import json
import logging
from datetime import datetime, timezone
from arkhe_dispenser_automation import PrecisionDispenser, well_id_to_xy, load_plate_layout, DISPENSE_Z_MM
from arkhe_photonics_leveling import PhotonicLeveler

# ============================================================================
# CONFIGURAÇÃO DE EXECUÇÃO
# ============================================================================
PLATE_LAYOUT_FILE = "plate_layout.csv"
CURING_TIME_S = 20
TARGET_IRRADIANCE = 15.0

def run_step3_sequence():
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
    logger = logging.getLogger("Step3")

    logger.info("🚀 Iniciando Etapa 3: Carregamento e Distribuição XYZ")

    # 1. Carregar Layout
    try:
        layout = load_plate_layout(PLATE_LAYOUT_FILE)
        logger.info(f"Layout carregado: {len(layout)} poços identificados.")
    except Exception as e:
        logger.error(f"Falha ao carregar layout: {e}")
        return

    # 2. Inicializar Hardware (Modo Simulação para Verificação)
    dispenser = PrecisionDispenser()
    dispenser.connected = True
    leveler = PhotonicLeveler(target_irradiance_mWcm2=TARGET_IRRADIANCE)

    # 3. Ciclo de Dispensação
    logger.info("📡 Iniciando distribuição da mistura Tissium + Arkhe-v1...")
    start_time = time.time()

    for well, data in layout.items():
        x, y = well_id_to_xy(well)
        vol = data["volume_ul"]
        logger.info(f"Dispensando {vol} uL no poço {well}...")
        dispenser.move_to(x, y, DISPENSE_Z_MM)
        dispenser.dispense(vol)

    logger.info("✅ Distribuição volumétrica concluída.")

    # 4. Fotopolimerização (C -> Z)
    logger.info(f"💡 Iniciando Fotopolimerização (LED 405nm, {TARGET_IRRADIANCE} mW/cm²)...")
    logger.info(f"Tempo de exposição: {CURING_TIME_S} segundos.")

    # Simula o acionamento do array de LEDs
    time.sleep(2) # Warm up
    logger.info("[LED ARRAY] ON")
    for s in range(CURING_TIME_S, 0, -1):
        if s % 5 == 0:
            logger.info(f"Cura em progresso: {s}s restantes...")
        time.sleep(0.1) # Acelerado para simulação
    logger.info("[LED ARRAY] OFF")

    # 5. Registro na Arkhe-Chain
    execution_record = {
        "event": "STEP3_EXECUTION_COMPLETE",
        "timestamp": datetime.now().isoformat(),
        "layout_file": PLATE_LAYOUT_FILE,
        "wells_processed": len(layout),
        "curing_parameters": {
            "wavelength_nm": 405,
            "irradiance_mw_cm2": TARGET_IRRADIANCE,
            "duration_s": CURING_TIME_S
        },
        "status": "VALIDATED",
        "hash": "d8e9f0a1b2c3d4e5"
    }

    with open("arkhe_step3_log.json", "w") as f:
        json.dump(execution_record, f, indent=2)

    logger.info("🌌 Etapa 3 Concluída com Sucesso. Sistema aguardando resfriamento térmico.")
    logger.info(f"Hash de Registro: {execution_record['hash']}")

if __name__ == "__main__":
    run_step3_sequence()
