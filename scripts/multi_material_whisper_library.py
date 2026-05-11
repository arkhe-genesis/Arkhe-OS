# multi_material_whisper_library.py — Biblioteca de sussurros para múltiplos scaffolds cristalinos

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Callable
from enum import Enum
import hashlib

class CrystalSystem(Enum):
    HEXAGONAL = "hexagonal"
    CUBIC = "cubic"
    TRIGONAL = "trigonal"

@dataclass
class PhononSignature:
    acoustic_modes_THz: List[float]
    optical_modes_THz: List[float]

@dataclass
class MaterialProperties:
    crystal_system: CrystalSystem
    lattice_constants_A: Dict[str, float]
    thermal_conductivity_W_mK: float
    bandgap_eV: float
    phonon_signature: PhononSignature

class MultiMaterialWhisperLibrary:
    """
    Biblioteca central de receitas de sussurro para múltiplos materiais cristalinos.
    """

    def __init__(self):
        self.material_database: Dict[str, MaterialProperties] = {}

    def register_material(self, name: str, properties: MaterialProperties):
        self.material_database[name] = properties

    def calibrate_new_material(self, material_name, crystal_structure):
        # Simula calibração via ressonância de fônons
        print(f"Calibrating pulse for {material_name} ({crystal_structure})...")
        return {"chirp": 850, "energy": 120}

if __name__ == "__main__":
    library = MultiMaterialWhisperLibrary()

    # Sapphire
    library.register_material("sapphire", MaterialProperties(
        crystal_system=CrystalSystem.HEXAGONAL,
        lattice_constants_A={'a': 4.7, 'c': 12.9},
        thermal_conductivity_W_mK=35,
        bandgap_eV=8.8,
        phonon_signature=PhononSignature(acoustic_modes_THz=[12, 18], optical_modes_THz=[65])
    ))

    # Diamond
    library.register_material("diamond", MaterialProperties(
        crystal_system=CrystalSystem.CUBIC,
        lattice_constants_A={'a': 3.5},
        thermal_conductivity_W_mK=2200,
        bandgap_eV=5.5,
        phonon_signature=PhononSignature(acoustic_modes_THz=[18, 35], optical_modes_THz=[133])
    ))

    print(f"Whisper Library initialized with {len(library.material_database)} materials.")
    recipe = library.calibrate_new_material("diamond", "cubic")
    print(f"Calibrated recipe for diamond: {recipe}")

    # Exotic Extension
    library.register_material("perovskite", MaterialProperties(
        crystal_system=CrystalSystem.TRIGONAL, # Approximate
        lattice_constants_A={'a': 6.2, 'c': 6.2},
        thermal_conductivity_W_mK=0.5,
        bandgap_eV=1.6,
        phonon_signature=PhononSignature(acoustic_modes_THz=[5], optical_modes_THz=[15])
    ))
    print(f"Exotic material registered: perovskite")
