# =========================================================
# RuView-Otico: Fibra Cherenkov + SiPM
# Substrato 390-OPT
# =========================================================
import math, random, time
from core.constants import C, CHERENKOV_THRESHOLD_MEV, PHOTONS_PER_MEV_M

class FiberCherenkovSensor:
    def __init__(self, length_m: float = 10.0):
        self.fiber_type = "OM3/OM4 multimodo 50um"
        self.core_diameter_um = 50
        self.numerical_aperture = 0.2
        self.refractive_index = 1.48
        self.length_m = length_m
        self.cherenkov_threshold_MeV = CHERENKOV_THRESHOLD_MEV
        self.photons_per_MeV_m = PHOTONS_PER_MEV_M
        self.coupling_efficiency = 0.3
        self.attenuation_db_km = 3.0
        self.ria_coefficient_db_km_krad = 10.0
        self.sipm_pde = 0.25
        self.sipm_gain = 1e6
        self.dark_count_rate_hz = 100e3

    def compute_cherenkov_photons(self, energy_MeV: float) -> float:
        if energy_MeV < self.cherenkov_threshold_MeV:
            return 0.0
        return (self.photons_per_MeV_m * energy_MeV *
                self.length_m * self.coupling_efficiency)

    def detect_pulse(self, energy_MeV: float) -> dict:
        photons = self.compute_cherenkov_photons(energy_MeV)
        detected = photons * self.sipm_pde
        amplitude_mV = detected * 0.5
        amplitude_mV += random.gauss(0, 3.0)  # ruido

        return {
            "timestamp_ns": int(time.time_ns()),
            "photons_cherenkov": photons,
            "photons_detected": detected,
            "amplitude_mV": max(0, amplitude_mV),
            "energy_MeV": energy_MeV,
            "above_threshold": amplitude_mV > 15.0
        }

    def classify_pulse(self, amplitude_mV: float, width_ns: float) -> dict:
        if amplitude_mV > 1000 and width_ns < 10:
            return {"class": "ALPHA", "confidence": 0.98}
        elif amplitude_mV > 200 and width_ns < 50:
            return {"class": "BETA_GAMMA", "confidence": 0.92}
        elif width_ns > 50:
            return {"class": "MUON", "confidence": 0.95}
        return {"class": "UNKNOWN", "confidence": 0.4}

    def get_spec(self) -> dict:
        return {
            "fiber_type": self.fiber_type,
            "core_um": self.core_diameter_um,
            "length_m": self.length_m,
            "cherenkov_threshold_MeV": self.cherenkov_threshold_MeV,
            "photons_per_MeV_m": self.photons_per_MeV_m,
            "coupling_efficiency": self.coupling_efficiency,
            "sipm_pde": self.sipm_pde,
            "sipm_gain": self.sipm_gain,
            "dark_count_hz": self.dark_count_rate_hz
        }
