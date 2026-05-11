#!/usr/bin/env python3
"""
arkhe_dispenser_automation.py
Arkhe(n) – Automated dispensing of Tissium+Arkhe-v1 mixture into 96‑well plates.
Maps nerve type/volume to well coordinates and controls precision dispenser.
"""

import csv
import json
import time
import argparse
import logging
from typing import Dict, Tuple, Optional
from dataclasses import dataclass

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================
WELL_PITCH_MM = 9.0
ORIGIN_A1_MM = (14.0, 11.0)   # X, Y (ajustar conforme hardware)
DISPENSE_Z_MM = 2.0           # altura da ponta acima do fundo do poço
DEFAULT_CONC_U_M = 10.0       # µM alvo
PEPTIDE_MW = 2841.0           # g/mol

# Tabela de dosagem por tipo de nervo (volume em µL)
DOSAGE_TABLE = {
    "Ciatico_Rato": {"volume_ul": 31.4, "peptide_ug": 0.89},
    "Ciatico_Humano": {"volume_ul": 259, "peptide_ug": 7.36},
    "Mediano_Humano": {"volume_ul": 88, "peptide_ug": 2.50},
    "Ulnar_Humano": {"volume_ul": 66, "peptide_ug": 1.87},
    "Femoral_Humano": {"volume_ul": 148, "peptide_ug": 4.20},
    "Tibial_Humano": {"volume_ul": 204, "peptide_ug": 5.80},
    "Radial_Humano": {"volume_ul": 113, "peptide_ug": 3.21},
    "Peroneiro_Humano": {"volume_ul": 88, "peptide_ug": 2.50},
    "Digital": {"volume_ul": 44, "peptide_ug": 1.25},
    "Controle": {"volume_ul": 50, "peptide_ug": 0.0},
}

# ============================================================================
# CLASSE DE HARDWARE (SIMULAÇÃO)
# ============================================================================
class PrecisionDispenser:
    """Simula um dispensador de precisão (Braço XYZ + bomba). Substituir por driver real."""
    def __init__(self, port: str = "/dev/ttyACM0"):
        self.connected = False
        self.current_position = (0, 0, 0)  # mm
        logging.info(f"Initializing dispenser on {port} (simulation mode)")

    def connect(self):
        self.connected = True
        logging.info("Dispenser connected.")

    def disconnect(self):
        self.connected = False
        logging.info("Dispenser disconnected.")

    def move_to(self, x: float, y: float, z: float):
        """Move para coordenada XYZ (mm)."""
        if not self.connected:
            raise RuntimeError("Dispenser not connected")
        self.current_position = (x, y, z)
        logging.info(f"Moving to X={x:.2f}, Y={y:.2f}, Z={z:.2f}")
        time.sleep(0.01)  # simula movimento (acelerado)

    def dispense(self, volume_ul: float):
        """Dispense volume em microlitros."""
        if not self.connected:
            raise RuntimeError("Dispenser not connected")
        logging.info(f"Dispensing {volume_ul:.2f} µL")
        time.sleep(0.01)  # simula tempo de dispensação (acelerado)
        return True

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================
def well_id_to_xy(well_id: str) -> Tuple[float, float]:
    """Converte ID de poço (ex: 'A1', 'H12') para coordenadas X, Y."""
    row_letter = well_id[0].upper()
    col_num = int(well_id[1:])
    row_index = ord(row_letter) - ord('A')
    col_index = col_num - 1
    x = ORIGIN_A1_MM[0] + col_index * WELL_PITCH_MM
    y = ORIGIN_A1_MM[1] + row_index * WELL_PITCH_MM
    return x, y

def calculate_volume_by_geometry(diameter_mm: float, gap_mm: float, wall_thickness_mm: float = 0.5, overlap_mm: float = 2.5) -> float:
    """
    Calcula volume do manguito (cilindro oco) com base na geometria do nervo.
    """
    L = gap_mm + 2 * overlap_mm
    r_in = diameter_mm / 2.0
    r_out = r_in + wall_thickness_mm
    volume_mm3 = 3.14159 * (r_out**2 - r_in**2) * L
    return float(volume_mm3)  # µL (1 mm³ = 1 µL)

def load_plate_layout(csv_file: str) -> Dict[str, dict]:
    """
    Lê ficheiro CSV com colunas: well, nerve_type, [custom_volume_ul].
    Exemplo:
        well,nerve_type
        A1,ciatico_rato
        B2,mediano_humano
        C3,digital
    """
    layout = {}
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            well = row['well'].strip()
            nerve = row.get('nerve_type', '').strip()
            if nerve in DOSAGE_TABLE:
                volume_ul = DOSAGE_TABLE[nerve]["volume_ul"]
            else:
                # Se não estiver na tabela, calcular por geometria (espera colunas diam_mm, gap_mm)
                if 'diam_mm' in row and 'gap_mm' in row:
                    diam = float(row['diam_mm'])
                    gap = float(row['gap_mm'])
                    volume_ul = calculate_volume_by_geometry(diam, gap)
                else:
                    # Tenta pegar volume_ul direto
                    volume_ul = float(row.get('volume_ul', 0))
                    if volume_ul == 0:
                        raise ValueError(f"Unknown nerve type '{nerve}' and no geometry or volume provided for well {well}")
            layout[well] = {"volume_ul": volume_ul, "nerve_type": nerve or "custom"}
    return layout

# ============================================================================
# REGISTRO NA ARKHE‑CHAIN (SIMULAÇÃO)
# ============================================================================
def log_to_arkhe_chain(record: dict):
    """Registra evento de dispensação (simulação). Em produção, chamaria API real."""
    log_entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "protocol": "ARKHE_DISPENSE_V1",
        **record
    }
    with open("arkhe_dispense_log.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    # Reduzindo verbosidade no log padrão
    # logging.info(f"Arkhe-Chain logged: {log_entry['well']} - {log_entry['volume_ul']} µL")

# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================
def main():
    parser = argparse.ArgumentParser(description="Automated dispenser for Arkhe-v1/Tissium mixture")
    parser.add_argument("--layout", type=str, required=True, help="CSV file with plate layout (well, nerve_type)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate only, do not move hardware")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level.upper()), format='%(asctime)s - %(levelname)s - %(message)s')

    # Carregar layout da placa
    try:
        layout = load_plate_layout(args.layout)
    except Exception as e:
        logging.error(f"Failed to load layout: {e}")
        return

    logging.info(f"Loaded layout for {len(layout)} wells.")

    # Conectar ao hardware (se não dry-run)
    dispenser = PrecisionDispenser()
    if not args.dry_run:
        dispenser.connect()
    else:
        dispenser.connected = True # Enable simulation mode in the class
        logging.info("DRY RUN mode – simulating hardware commands.")

    # Processar cada poço
    for well, data in layout.items():
        volume_ul = data["volume_ul"]
        nerve = data["nerve_type"]
        x, y = well_id_to_xy(well)
        logging.debug(f"Processing well {well} (nerve: {nerve}) -> volume {volume_ul:.2f} µL")

        try:
            dispenser.move_to(x, y, DISPENSE_Z_MM)
            dispenser.dispense(volume_ul)
        except Exception as e:
            logging.error(f"Failed to dispense at well {well}: {e}")
            continue

        # Registar na Arkhe‑Chain
        log_to_arkhe_chain({
            "well": well,
            "nerve_type": nerve,
            "volume_ul": volume_ul,
            "x_mm": x,
            "y_mm": y,
            "dry_run": args.dry_run
        })

    if not args.dry_run:
        dispenser.disconnect()

    logging.info("Dispensing completed.")

if __name__ == "__main__":
    main()
