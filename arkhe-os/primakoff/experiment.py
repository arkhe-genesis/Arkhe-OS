import math, random, time, hashlib, json
from core.constants import C, MU_0, M_AXION_EV, G_AYY_GEV_INV

class PrimakoffExperiment:
    """Experimento completo de busca de axions."""

    def __init__(self,
                 coil_length_m: float = 3.0,
                 coil_field_t: float = 0.57,
                 beam_energy_gev: float = 50.0,
                 days: int = 100):
        self.coil_length_m = coil_length_m
        self.coil_field_t = coil_field_t
        self.beam_energy_gev = beam_energy_gev
        self.days = days
        self.electrons_per_spill = 1e7
        self.spills_per_day = 1e5
        self.total_electrons = (self.electrons_per_spill *
                                self.spills_per_day * days)
        self.snspd_efficiency = 0.92
        self.veto_efficiency = 0.995
        self.background_per_day = 0.5
        self.events_detected = []

    def compute_primakoff_probability(self) -> float:
        """Probabilidade de conversao gamma->a via efeito Primakoff."""
        return (G_AYY_GEV_INV * self.coil_field_t * self.coil_length_m / 2)**2 / 4

    def compute_signal(self) -> float:
        """Eventos de sinal esperados."""
        P = self.compute_primakoff_probability()
        wall_transmission = 1e-20
        return (self.total_electrons * 0.1 * P * wall_transmission *
                P * self.snspd_efficiency)

    def compute_background(self) -> float:
        """Fundo apos veto."""
        return self.background_per_day * self.days * (1 - self.veto_efficiency)

    def compute_significance(self) -> float:
        """Significancia estatistica do sinal."""
        S = self.compute_signal()
        B = self.compute_background()
        if S + B <= 0:
            return 0.0
        return S / math.sqrt(S + B)

    def run_simulation(self) -> dict:
        """Executa simulacao completa do experimento."""
        signal = self.compute_signal()
        background = self.compute_background()
        observed = random.gauss(signal + background,
                               math.sqrt(signal + background))
        sigma = self.compute_significance()

        return {
            "experiment": "PRIMAKOFF-GOLD",
            "coil_length_m": self.coil_length_m,
            "coil_field_t": self.coil_field_t,
            "beam_energy_gev": self.beam_energy_gev,
            "days": self.days,
            "total_electrons": self.total_electrons,
            "primakoff_probability": self.compute_primakoff_probability(),
            "signal_events": round(signal, 1),
            "background_events": round(background, 2),
            "observed_events": round(observed, 0),
            "significance_sigma": round(sigma, 1),
            "discovery": sigma >= 5.0,
            "phi_c": min(0.999, 0.9 + sigma / 10)
        }

    def calibrate_with_source(self, source: str, energy_MeV: float,
                              counts: int) -> dict:
        """Calibracao com fonte radioativa."""
        return {
            "source": source,
            "energy_MeV": energy_MeV,
            "counts": counts,
            "efficiency": round(counts / (3700 * 3600 * 0.85), 4),
            "calibration_factor_mV_per_keV": round(0.22, 3)
        }

    def get_seal(self) -> str:
        result = self.run_simulation()
        record = {
            "substrate": 396,
            "experiment": "PRIMAKOFF-GOLD",
            "phi_c": result["phi_c"],
            "significance": result["significance_sigma"],
            "timestamp": time.time()
        }
        return hashlib.sha3_256(
            json.dumps(record, sort_keys=True).encode()
        ).hexdigest()