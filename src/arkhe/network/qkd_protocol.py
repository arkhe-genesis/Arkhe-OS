import time
import hashlib
import json
import numpy as np
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum, auto

class QKDProtocol(Enum):
    BB84 = auto()
    E91 = auto()
    TF_QKD = auto()
    SATELLITE_RELAY = auto()

@dataclass
class QKDSession:
    session_id: str
    protocol: QKDProtocol
    satellite_id: str
    ground_station_a: str
    ground_station_b: str
    key_length_bits: int
    error_rate: float
    secret_key_rate_bps: float
    temporal_anchor: Optional[str]

class QKDKeyDistribution:
    PHYSICAL_PARAMS = {
        "wavelength_nm": 1550,
        "satellite_altitude_km": 500,
        "beam_divergence_urad": 10,
        "atmospheric_loss_db": 3.0,
        "detector_efficiency": 0.85,
        "dark_count_rate_hz": 100,
    }

    def __init__(self, satellite_id: str, ground_stations: List[str]):
        self.satellite_id = satellite_id
        self.ground_stations = ground_stations
        self.active_sessions = {}
        self.shared_keys = {}

    async def establish_qkd_session(self, station_a: str, station_b: str, protocol: QKDProtocol = QKDProtocol.E91, key_length: int = 256) -> QKDSession:
        session_id = f"qkd_{hashlib.sha3_256(f'{station_a}{station_b}{time.time()}'.encode()).hexdigest()[:12]}"

        params = self.PHYSICAL_PARAMS
        free_space_loss = 20 * np.log10(4 * np.pi * params["satellite_altitude_km"] * 1e3 / (params["wavelength_nm"] * 1e-9))
        total_loss_db = free_space_loss + params["atmospheric_loss_db"]
        source_rate = 1e6
        detection_prob = params["detector_efficiency"] * 10**(-total_loss_db / 10)
        raw_key_rate = source_rate * detection_prob

        protocol_efficiency = {QKDProtocol.BB84: 0.5, QKDProtocol.E91: 0.45, QKDProtocol.TF_QKD: 0.6, QKDProtocol.SATELLITE_RELAY: 0.35}.get(protocol, 0.4)
        secret_key_rate = raw_key_rate * protocol_efficiency * 0.8

        base_qber = 0.02
        atmospheric_noise = np.random.exponential(0.01)
        qber = base_qber + atmospheric_noise

        secret_key = hashlib.sha3_256(f"{session_id}{time.time_ns()}".encode()).digest()
        self.shared_keys[session_id] = secret_key

        key_hash = hashlib.sha3_256(secret_key).hexdigest()
        anchor = hashlib.sha3_256(json.dumps({
            "session_id": session_id,
            "key_hash": key_hash,
            "stations": [station_a, station_b],
            "satellite": self.satellite_id,
            "timestamp": time.time(),
            "protocol": "QKD",
        }, sort_keys=True).encode()).hexdigest()[:16]

        session = QKDSession(
            session_id=session_id,
            protocol=protocol,
            satellite_id=self.satellite_id,
            ground_station_a=station_a,
            ground_station_b=station_b,
            key_length_bits=key_length,
            error_rate=qber,
            secret_key_rate_bps=max(0, secret_key_rate),
            temporal_anchor=anchor
        )
        self.active_sessions[session_id] = session
        return session
