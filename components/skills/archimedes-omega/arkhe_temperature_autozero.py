#!/usr/bin/env python3
"""
arkhe_temperature_autozero.py
Arkhe(n) – Auto‑zero calibration for plate temperature sensors.
Executes before photopolymerization to establish baseline.
"""

import json
import time
import numpy as np
import logging
from datetime import datetime, timezone
from typing import List, Dict

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================
N_SAMPLES = 10          # Número de leituras por sensor
SAMPLE_INTERVAL = 0.1   # segundos entre leituras (acelerado para simulação)
REFERENCE_TEMP = 25.0   # °C (temperatura ambiente medida por termístor de precisão)
MAX_STD_DEV = 0.2       # °C (limite de estabilidade)

# Mapeamento dos sensores (ex.: 8 sensores, um por linha da placa)
SENSOR_IDS = ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"]

# ============================================================================
# SIMULAÇÃO DA LEITURA DE HARDWARE
# ============================================================================
class TemperatureSensor:
    """Simula um sensor de temperatura (termopar/termístor)."""
    @staticmethod
    def read(sensor_id: str) -> float:
        # Simula leitura com pequeno ruído e desvio sistemático
        base_temp = 25.0
        # Simula desvio sistemático diferente para cada sensor
        offset_map = {"S1": 0.0, "S2": -0.2, "S3": +0.1, "S4": -0.3,
                      "S5": +0.2, "S6": -0.1, "S7": +0.3, "S8": 0.0}
        noise = np.random.normal(0, 0.05)
        return float(base_temp + offset_map.get(sensor_id, 0.0) + noise)

# ============================================================================
# FUNÇÕES DE CALIBRAÇÃO
# ============================================================================
def auto_zero_sensors(sensor_ids: List[str], n_samples: int = N_SAMPLES,
                      interval: float = SAMPLE_INTERVAL) -> Dict[str, float]:
    """
    Executa a rotina de auto‑zero para cada sensor.
    Retorna dicionário com offsets (ΔT = T_ref - T_raw_média).
    """
    logging.info("Iniciando rotina de auto‑zero dos sensores de temperatura...")
    offsets = {}
    for sid in sensor_ids:
        readings = []
        for _ in range(n_samples):
            temp = TemperatureSensor.read(sid)
            readings.append(temp)
            time.sleep(interval)
        mean_temp = np.mean(readings)
        std_temp = np.std(readings)
        logging.info(f"Sensor {sid}: média = {mean_temp:.2f} °C, std = {std_temp:.3f} °C")
        if std_temp > MAX_STD_DEV:
            logging.warning(f"Sensor {sid} apresenta alta variabilidade ({std_temp:.3f} °C).")
        offset = REFERENCE_TEMP - mean_temp
        offsets[sid] = float(offset)
        logging.info(f"Offset calculado para {sid}: {offset:+.2f} °C")
    return offsets

def save_calibration(offsets: Dict[str, float], filename: str = "temp_calibration.json"):
    """Salva os offsets num ficheiro JSON para uso posterior."""
    cal_data = {
        "timestamp": datetime.now().isoformat(),
        "reference_temp_c": float(REFERENCE_TEMP),
        "n_samples": N_SAMPLES,
        "offsets": offsets
    }
    with open(filename, "w") as f:
        json.dump(cal_data, f, indent=2)
    logging.info(f"Calibração salva em {filename}")

def run_autozero_and_record():
    """Executa a rotina, salva a calibração e regista na Arkhe‑Chain."""
    offsets = auto_zero_sensors(SENSOR_IDS)
    save_calibration(offsets)
    # Registo na Arkhe‑Chain (simulação)
    import hashlib
    cal_json = json.dumps(offsets, sort_keys=True)
    cal_hash = hashlib.sha256(cal_json.encode()).hexdigest()[:16]
    print(f"[Arkhe-Chain] Calibração registada. Hash: {cal_hash}")
    return offsets

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    run_autozero_and_record()
