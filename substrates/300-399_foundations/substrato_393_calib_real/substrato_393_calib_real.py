#!/usr/bin/env python3
"""
ARKHE OS — Protocolo de Calibração Radioativa
Substrato 393: Calibração com fontes reais Am-241 e Cs-137
"""

import math
import random
from typing import Dict, List, Tuple
from dataclasses import dataclass
import hashlib
import json
import time

@dataclass
class RadioactiveSource:
    name: str
    half_life_years: float
    decay_mode: str
    energy_mev: float
    activity_bq: float
    intensity_percent: float
    distance_to_fiber_mm: float = 5.0
    exposure_time_s: float = 3600

    def expected_counts(self, detector_efficiency: float = 0.01) -> float:
        return (self.activity_bq * detector_efficiency *
                self.exposure_time_s * (self.intensity_percent / 100))

    def dose_rate_usv_h(self) -> float:
        if "Cs" in self.name:
            return 33.0 * (self.activity_bq / 3700)
        elif "Am" in self.name:
            return 0.2 * (self.activity_bq / 3700)
        return 0.0

@dataclass
class ScintillatorConfig:
    scintillator_type: str = "EJ-200 (Plastic Scintillator)"
    dimensions_mm: Tuple[int, int, int] = (50, 50, 10)
    density_g_cm3: float = 1.023
    light_yield_photons_mev: int = 10000
    decay_time_ns: float = 2.1
    wavelength_max_nm: int = 425
    sipm_pde: float = 0.40
    sipm_gain: float = 1e6
    energy_resolution_percent: float = 8.5

class CalibrationProtocol:
    def __init__(self):
        self.steps = [
            "background_measurement",
            "Am241_measurement",
            "Cs137_measurement",
            "coincidence_verification",
            "energy_calibration",
            "efficiency_calculation"
        ]
        self.am241 = RadioactiveSource(
            name="Am-241", half_life_years=432.2, decay_mode="alpha",
            energy_mev=5.486, activity_bq=3700, intensity_percent=85.2
        )
        self.cs137 = RadioactiveSource(
            name="Cs-137", half_life_years=30.17, decay_mode="beta_gamma",
            energy_mev=0.662, activity_bq=3700, intensity_percent=94.7,
            distance_to_fiber_mm=10.0
        )
        self.scintillator = ScintillatorConfig()

    def calibration_curve(self, ruview_counts: List[float], ref_counts: List[float]) -> Dict:
        n = len(ruview_counts)
        if n < 2: return {"slope": 0, "intercept": 0, "r_squared": 0, "correlation": 0}

        mean_r = sum(ruview_counts) / n
        mean_ref = sum(ref_counts) / n

        numerator = sum((r - mean_r) * (ref - mean_ref) for r, ref in zip(ruview_counts, ref_counts))
        denominator = sum((ref - mean_ref)**2 for ref in ref_counts)

        a = numerator / denominator if denominator != 0 else 0
        b = mean_r - a * mean_ref

        ss_res = sum((r - (a * ref + b))**2 for r, ref in zip(ruview_counts, ref_counts))
        ss_tot = sum((r - mean_r)**2 for r in ruview_counts)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

        return {"slope": a, "intercept": b, "r_squared": r_squared, "correlation": math.sqrt(abs(r_squared))}

    def simulate_measurement(self, source: RadioactiveSource, detector_efficiency: float, is_ruview: bool = True) -> Dict:
        expected = source.expected_counts(detector_efficiency)
        observed = int(random.gauss(expected, math.sqrt(expected))) if expected > 0 else 0
        bg_rate = 10 if is_ruview else 1
        bg_counts = bg_rate * source.exposure_time_s

        return {
            "source": source.name,
            "energy_mev": source.energy_mev,
            "expected_counts": expected,
            "observed_counts": max(0, observed),
            "background_counts": bg_counts,
            "efficiency": detector_efficiency,
            "signal_to_background": observed / bg_counts if bg_counts > 0 else 0
        }

    def run_full_calibration(self) -> Dict:
        am241_ruview = self.simulate_measurement(self.am241, 0.008, True)
        cs137_ruview = self.simulate_measurement(self.cs137, 0.012, True)
        am241_ref = self.simulate_measurement(self.am241, 0.85, False)
        cs137_ref = self.simulate_measurement(self.cs137, 0.85, False)

        calib = self.calibration_curve(
            [am241_ruview['observed_counts'], cs137_ruview['observed_counts']],
            [am241_ref['observed_counts'], cs137_ref['observed_counts']]
        )

        kev_per_mv = abs(1.0 / calib['slope']) if calib['slope'] != 0 else 4.5

        return {
            "am241_ruview": am241_ruview,
            "cs137_ruview": cs137_ruview,
            "calibration_curve": calib,
            "energy_calibration": {"keV_per_mV": kev_per_mv}
        }

def generate_seal(results):
    record = {
        "substrate": "393",
        "keV_per_mV": results["energy_calibration"]["keV_per_mV"],
        "timestamp": time.time(),
        "status": "CANONIZED"
    }
    return hashlib.sha3_256(json.dumps(record, sort_keys=True).encode()).hexdigest()

def main():
    protocol = CalibrationProtocol()
    results = protocol.run_full_calibration()
    seal = generate_seal(results)

    print("=" * 70)
    print("ARKHE OS — PROTOCOLO DE CALIBRAÇÃO RADIOATIVA (Substrato 393)")
    print("=" * 70)
    print(f"Am-241 Observado: {results['am241_ruview']['observed_counts']}")
    print(f"Cs-137 Observado: {results['cs137_ruview']['observed_counts']}")
    print(f"Coeficiente Energético: {results['energy_calibration']['keV_per_mV']:.2f} keV/mV")
    print(f"\nSelo Canônico: {seal}")

if __name__ == "__main__":
    main()
