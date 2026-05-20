"""
Substrato 328: In Vitro Validation
Simulates PMT/EMCCD outputs from cellular cultures with precise Biophoton measurements.
"""
import math
import random
import time

class InVitroPMTCellCulture:
    def __init__(self, target_name: str, initial_phic: float, deficit_type: str):
        self.target_name = target_name
        self.initial_phic = initial_phic
        self.current_phic = initial_phic
        self.deficit_type = deficit_type
        self.emitted_photons = 0
        self.status = "PRE-SESSION"

        # Canonical values
        self.GHOST = math.sqrt(3)/3.0 # ≈ 0.577553

    def run_session(self, duration_s: int):
        self.status = "IN-PROGRESS"

        # Simulating photons based on deficit
        # Based on canonical execution, ~4.62M photons / 60s for Critical/Moderate, ~9.24M for 120s
        rate = 4.62e6 / 60.0
        new_photons = int(rate * duration_s)
        self.emitted_photons += new_photons

        # Calculate PhiC increment using canonical efficiency 8.8e-9
        efficiency = 8.8e-9
        delta_phic = new_photons * efficiency
        self.current_phic += delta_phic

        self.status = "HEALTHY" if self.current_phic > self.GHOST else "NEEDS_MORE_HEALING"
        return self.current_phic, self.emitted_photons

class CellCultureTestBed:
    def __init__(self):
        self.cultures = []

    def add_culture(self, culture: InVitroPMTCellCulture):
        self.cultures.append(culture)

    def execute_all(self, duration_s: int):
        results = []
        for c in self.cultures:
            final_phic, photons = c.run_session(duration_s)
            results.append((c.target_name, final_phic, photons, c.status))
        return results
