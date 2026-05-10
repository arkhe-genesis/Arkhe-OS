import numpy as np
import json
from dataclasses import dataclass
from typing import List, Dict, Tuple

@dataclass
class NerveGeometry:
    name: str
    diameter_mm: float
    gap_mm: float
    wall_thickness_mm: float = 0.5
    anchorage_mm: float = 2.0 # Each side

    @property
    def total_length(self) -> float:
        return self.gap_mm + (2 * self.anchorage_mm)

    @property
    def volume_ul(self) -> float:
        r_out = (self.diameter_mm / 2.0) + self.wall_thickness_mm
        r_in = self.diameter_mm / 2.0
        # Volume = PI * (R_out^2 - R_in^2) * L
        vol_mm3 = np.pi * (r_out**2 - r_in**2) * self.total_length
        return float(vol_mm3) # 1 mm^3 = 1 uL

class PrecisionDispenser:
    """
    Automates the precision dispensing for the Arkhe-Link 96-well plate assays.
    Maps nerve-specific volumes to XYZ coordinates.
    """
    def __init__(self, start_x: float = 10.0, start_y: float = 10.0, z_height: float = 5.0, pitch: float = 9.0):
        self.start_x = start_x
        self.start_y = start_y
        self.z_height = z_height
        self.pitch = pitch # Standard 96-well plate pitch is 9mm

    def get_well_coordinates(self, well_index: int) -> Tuple[float, float, float]:
        """
        Converts a well index (0-95) to XYZ coordinates.
        Index 0 = A1, 1 = A2 ... 11 = A12, 12 = B1 ...
        """
        row = well_index // 12
        col = well_index % 12
        x = self.start_x + (col * self.pitch)
        y = self.start_y + (row * self.pitch)
        return (round(x, 2), round(y, 2), round(self.z_height, 2))

    def generate_dispense_program(self, geometries: List[NerveGeometry], wells_per_type: int = 3) -> List[Dict]:
        """
        Generates a sequence of dispense operations.
        """
        program = []
        well_counter = 0

        for geo in geometries:
            for _ in range(wells_per_type):
                if well_counter >= 96:
                    break

                coords = self.get_well_coordinates(well_counter)
                well_label = f"{chr(65 + (well_counter // 12))}{ (well_counter % 12) + 1 }"

                operation = {
                    "step": len(program) + 1,
                    "well": well_label,
                    "target": geo.name,
                    "coordinates": {
                        "x": coords[0],
                        "y": coords[1],
                        "z": coords[2]
                    },
                    "volume_ul": round(geo.volume_ul, 2),
                    "peptide_arkhe_v1_ug": round(geo.volume_ul * 0.05, 3), # Target 50 ug/mL = 0.05 ug/uL
                    "status": "PENDING"
                }
                program.append(operation)
                well_counter += 1

        return program

def export_automation_script(program: List[Dict], filename: str = "dispenser_automation_v1.json"):
    with open(filename, 'w') as f:
        json.dump({
            "protocol": "ARKHE_DISPENSER_V1",
            "metadata": {
                "peptide": "Arkhe-v1",
                "concentration_ug_ul": 0.05,
                "plate_type": "96_WELL_PRECISION"
            },
            "sequence": program
        }, f, indent=2)
    print(f"✅ Script de automação salvo em {filename}")

if __name__ == "__main__":
    # Define os alvos anatômicos conforme a planilha
    targets = [
        NerveGeometry("Ciático (rato)", 1.5, 5.0, anchorage_mm=2.5), # Total L=10
        NerveGeometry("Mediano (humano)", 3.0, 10.0, anchorage_mm=3.0), # Total L=16
        NerveGeometry("Ulnar (humano)", 2.5, 8.0, anchorage_mm=3.0), # Total L=14
        NerveGeometry("Micro-Nervo Digital", 1.0, 3.0, anchorage_mm=2.0) # Total L=7
    ]

    dispenser = PrecisionDispenser()
    program = dispenser.generate_dispense_program(targets, wells_per_type=6)
    export_automation_script(program)
