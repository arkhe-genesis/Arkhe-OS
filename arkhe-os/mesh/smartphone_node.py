# =========================================================
# No de smartphone para a rede mesh
# Substrato 397
# =========================================================
import random, math, time, hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from enum import Enum

class ParticleType(Enum):
    MUON = "muon"
    ELECTRON = "electron"
    PHOTON = "photon"
    ALPHA = "alpha"
    NOISE = "noise"

@dataclass
class SensorConfig:
    efficiency: float = 0.01
    false_positive_rate: float = 0.005
    range_m: float = 10.0

@dataclass
class Event:
    node_id: int
    timestamp: float
    particle_type: ParticleType
    confidence: float
    sensors_triggered: List[str]
    location: Tuple[float, float]
    signature: str = ""

    def __post_init__(self):
        if not self.signature:
            payload = f"{self.node_id}|{self.timestamp}|{self.particle_type.value}"
            self.signature = hashlib.sha3_256(payload.encode()).hexdigest()[:16]

@dataclass
class SmartphoneNode:
    node_id: int
    lat: float
    lon: float
    sensors: Dict[str, SensorConfig] = field(default_factory=dict)
    neighbors: List[int] = field(default_factory=list)
    events_detected: int = 0
    events_shared: int = 0
    model_accuracy: float = 0.85

    def __post_init__(self):
        if not self.sensors:
            self.sensors = {
                "cmos": SensorConfig(0.003, 0.001, 0),
                "wifi": SensorConfig(0.010, 0.020, 10),
                "bluetooth": SensorConfig(0.002, 0.005, 1),
                "5g": SensorConfig(0.015, 0.010, 50),
                "accel": SensorConfig(0.001, 0.003, 0),
                "mic": SensorConfig(0.0005, 0.010, 0)
            }

    def detect(self, particle: ParticleType = ParticleType.MUON) -> Optional[Event]:
        triggered = []

        for sensor_name, config in self.sensors.items():
            eff = config.efficiency * self._particle_factor(particle)
            if random.random() < eff:
                triggered.append(sensor_name)
            elif random.random() < config.false_positive_rate:
                triggered.append(f"{sensor_name}_noise")

        real_hits = [t for t in triggered if not t.endswith("_noise")]

        if len(real_hits) >= 2:
            confidence = min(0.98, 0.85 + 0.10 * len(real_hits))
            self.events_detected += 1
            return Event(
                node_id=self.node_id,
                timestamp=time.time(),
                particle_type=particle,
                confidence=confidence,
                sensors_triggered=real_hits,
                location=(self.lat, self.lon)
            )
        elif len(real_hits) == 1 and random.random() < 0.3:
            return Event(
                node_id=self.node_id,
                timestamp=time.time(),
                particle_type=ParticleType.NOISE,
                confidence=0.5,
                sensors_triggered=real_hits,
                location=(self.lat, self.lon)
            )

        return None

    def _particle_factor(self, particle: ParticleType) -> float:
        factors = {
            ParticleType.MUON: 1.0,
            ParticleType.ELECTRON: 0.8,
            ParticleType.PHOTON: 0.3,
            ParticleType.ALPHA: 1.5,
            ParticleType.NOISE: 0.1
        }
        return factors.get(particle, 1.0)

    def share_event(self, event: Event, ttl: int = 3) -> List[int]:
        if ttl <= 0 or event.confidence < 0.85:
            return []

        recipients = []
        for neighbor_id in self.neighbors:
            if random.random() < 0.7:
                recipients.append(neighbor_id)
                self.events_shared += 1

        return recipients
