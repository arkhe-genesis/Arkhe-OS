# =========================================================
# RuView-RF: Detector CSI WiFi (ESP32-S3)
# Substrato 389
# =========================================================
import random, time, math, hashlib
from dataclasses import dataclass, field

@dataclass
class CSIEvent:
    timestamp_ns: int
    node_id: int
    subcarrier_perturbations: list
    particle_type: str
    energy_deposit_keV: float
    confidence: float

class RuViewRF:
    """Sensor Fantasma - deteccao de particulas via WiFi CSI."""

    def __init__(self, n_nodes: int = 4):
        self.n_nodes = n_nodes
        self.links = n_nodes * (n_nodes - 1)
        self.subcarriers = 168
        self.channels = 6
        self.total_dimensions = self.channels * self.subcarriers
        self.threshold = 200
        self.events_detected = []
        self.background_rate_hz = 0.1
        self.cosmic_rate_hz = 0.01

    def detect_event(self) -> dict:
        """Simula deteccao de particula via perturbacao CSI."""
        particle = random.choices(
            ["muon", "electron", "photon", "neutron"],
            weights=[0.01, 0.02, 0.05, 0.001]
        )[0]

        if particle == "muon":
            amplitude = random.gauss(800, 100)
            integral = random.gauss(5000, 500)
        elif particle == "electron":
            amplitude = random.gauss(400, 80)
            integral = random.gauss(2000, 300)
        elif particle == "photon":
            amplitude = random.gauss(200, 50)
            integral = random.gauss(800, 200)
        else:
            amplitude = random.gauss(50, 20)
            integral = random.gauss(200, 100)

        event = {
            "timestamp_ns": int(time.time_ns()),
            "amplitude": max(0, int(amplitude)),
            "integral": max(0, int(integral)),
            "particle_type": particle,
            "above_threshold": amplitude > self.threshold
        }
        self.events_detected.append(event)
        return event

    def classify(self, event: dict) -> dict:
        """Classificacao por largura do pico CSI."""
        ratio = event["integral"] / event["amplitude"] if event["amplitude"] > 0 else 0
        if event["amplitude"] > 600 and ratio > 5:
            return {"class": "MUON", "confidence": 0.92}
        elif 300 < event["amplitude"] < 700 and 3 < ratio < 7:
            return {"class": "ELECTRON", "confidence": 0.88}
        elif event["amplitude"] < 400 and ratio < 4:
            return {"class": "PHOTON", "confidence": 0.85}
        elif event["amplitude"] < 100:
            return {"class": "NEUTRON", "confidence": 0.75}
        return {"class": "UNKNOWN", "confidence": 0.3}

    def get_status(self) -> dict:
        return {
            "n_nodes": self.n_nodes,
            "links": self.links,
            "dimensions": self.total_dimensions,
            "events_total": len(self.events_detected),
            "threshold": self.threshold
        }
