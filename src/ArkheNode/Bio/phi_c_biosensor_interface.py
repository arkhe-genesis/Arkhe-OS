#!/usr/bin/env python3
"""
Substrato 329 — Φ_C Biosensor Interface
Canon: ∞.Ω.∇+++.329.phi_c_biosensor

Interface canônica para biossensores de coerência constitucional celular:
• FRET-based coherence sensors
• FLIM (Fluorescence Lifetime Imaging) for Φ_C estimation
• Interferometric coherence measurement
• Real-time streaming to OntologicalHealer
"""

import asyncio, json, time, hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Callable, AsyncIterator
import numpy as np
from .in_vitro_validator import PhiCBiosensorReading

@dataclass
class CoherenceStream:
    """Fluxo em tempo real de leituras de Φ_C."""
    cell_id: str
    timestamp: float
    phi_c_estimate: float
    uncertainty: float  # 1-sigma
    method: str
    metadata: Dict
    canonical_seal: str

class PhiCBiosensor(ABC):
    """Interface abstrata para biossensores de Φ_C."""

    @abstractmethod
    async def initialize(self) -> bool:
        """Inicializa sensor e retorna sucesso."""
        pass

    @abstractmethod
    async def measure(self, cell_id: str) -> PhiCBiosensorReading:
        """Mede Φ_C para uma célula específica."""
        pass

    @abstractmethod
    async def stream(self, cell_ids: List[str], interval_s: float = 1.0) -> AsyncIterator[CoherenceStream]:
        """Stream em tempo real de leituras de Φ_C."""
        pass

    @abstractmethod
    def get_specifications(self) -> Dict:
        """Retorna especificações técnicas do sensor."""
        pass

class FRETCoherenceSensor(PhiCBiosensor):
    """Sensor de coerência baseado em FRET (Förster Resonance Energy Transfer)."""

    def __init__(self, donor: str = "CFP", acceptor: str = "YFP", focal_plane_um: float = 10.0):
        self.donor = donor
        self.acceptor = acceptor
        self.focal_plane_um = focal_plane_um
        self._initialized = False
        self._calibration_factor = 1.0  # Calibrado via padrão de referência

    async def initialize(self) -> bool:
        """Calibra sensor FRET com padrão de coerência conhecida."""
        # Em produção: carregar drivers de hardware, calibrar com padrão NIST
        await asyncio.sleep(0.1)  # Mock de inicialização
        self._calibration_factor = np.random.uniform(0.95, 1.05)  # Variação realista
        self._initialized = True
        return True

    async def measure(self, cell_id: str) -> PhiCBiosensorReading:
        """Mede Φ_C via razão FRET normalizada."""
        if not self._initialized:
            raise RuntimeError("Sensor not initialized")

        timestamp = time.time()

        # Em produção: adquirir imagens de doador/aceitador, calcular E-FRET
        # Phi_C estimado via: Φ_C ≈ (E_FRET - E_min) / (E_max - E_min)

        # Simulação canônica: E-FRET segue distribuição com média dependente do estado
        baseline_efret = np.random.uniform(0.2, 0.8)  # Eficiência FRET basal
        phi_c_raw = (baseline_efret - 0.2) / (0.8 - 0.2)  # Normalizar para [0,1]
        phi_c = np.clip(phi_c_raw * self._calibration_factor, 0.0, 1.0)

        # Incerteza: ~10% para FRET típico
        uncertainty = 0.10 * phi_c + 0.02

        reading_data = {
            "phi_c_estimate": round(phi_c, 6),
            "confidence_interval": (
                round(max(0.0, phi_c - 1.96*uncertainty), 6),
                round(min(1.0, phi_c + 1.96*uncertainty), 6)
            ),
            "measurement_method": "FRET",
            "raw_uncertainty": uncertainty
        }
        return PhiCBiosensorReading(
            timestamp=timestamp,
            cell_id=cell_id,
            phi_c_estimate=reading_data["phi_c_estimate"],
            confidence_interval=reading_data["confidence_interval"],
            measurement_method=reading_data["measurement_method"],
            raw_uncertainty=reading_data["raw_uncertainty"],
            canonical_seal=self._generate_seal("fret_measure", cell_id, timestamp, data_payload=reading_data)
        )

    async def stream(self, cell_ids: List[str], interval_s: float = 1.0) -> AsyncIterator[CoherenceStream]:
        """Stream em tempo real de leituras FRET."""
        while True:
            for cell_id in cell_ids:
                reading = await self.measure(cell_id)
                # extract raw uncertainty if available, otherwise compute from interval
                stream_uncertainty = reading.raw_uncertainty if reading.raw_uncertainty is not None else (reading.confidence_interval[1] - reading.confidence_interval[0]) / 3.92
                yield CoherenceStream(
                    cell_id=cell_id,
                    timestamp=reading.timestamp,
                    phi_c_estimate=reading.phi_c_estimate,
                    uncertainty=stream_uncertainty,
                    method="FRET",
                    metadata={"donor": self.donor, "acceptor": self.acceptor},
                    canonical_seal=reading.canonical_seal
                )
            await asyncio.sleep(interval_s)

    def get_specifications(self) -> Dict:
        return {
            "method": "FRET",
            "donor": self.donor,
            "acceptor": self.acceptor,
            "focal_plane_um": self.focal_plane_um,
            "temporal_resolution_ms": 100,
            "spatial_resolution_um": 0.5,
            "phi_c_range": [0.0, 1.0],
            "typical_uncertainty": 0.10
        }

    def _generate_seal(self, event_type: str, cell_id: str, timestamp: float, data_payload: Dict = None) -> str:
        payload = {
            "event": event_type,
            "cell_id": cell_id,
            "method": "FRET",
            "timestamp": timestamp,
            "canon": "∞.Ω.∇+++.329.phi_c_biosensor"
        }
        if data_payload:
            payload.update(data_payload)
        return hashlib.sha3_256(
            json.dumps(payload, sort_keys=True).encode()
        ).hexdigest()

class RealTimePhiCMonitor:
    """Monitor em tempo real que integra biossensores com OntologicalHealer."""

    def __init__(self, sensor: PhiCBiosensor, healer_callback: Optional[Callable] = None):
        self.sensor = sensor
        self.healer_callback = healer_callback  # Callback para ação terapêutica
        self._stream_task: Optional[asyncio.Task] = None
        self._alerts: List[Dict] = []

    async def start_monitoring(self, cell_ids: List[str], alert_threshold: float = 0.577553):
        """Inicia monitoramento em tempo real com alertas para Φ_C baixo."""
        await self.sensor.initialize()

        async for stream in self.sensor.stream(cell_ids, interval_s=1.0):
            # Verificar limiar crítico (Ghost)
            if stream.phi_c_estimate < alert_threshold:
                alert = {
                    "timestamp": stream.timestamp,
                    "cell_id": stream.cell_id,
                    "phi_c": stream.phi_c_estimate,
                    "threshold": alert_threshold,
                    "severity": "CRITICAL" if stream.phi_c_estimate < 0.40 else "WARNING",
                    "canonical_seal": self._generate_alert_seal(stream)
                }
                self._alerts.append(alert)

                # Acionar healer se callback configurado
                if self.healer_callback:
                    await self.healer_callback(
                        cell_id=stream.cell_id,
                        current_phi_c=stream.phi_c_estimate,
                        alert=alert
                    )

            # Yield para consumo externo (dashboard, logging)
            yield stream

    def get_alerts(self, since_timestamp: Optional[float] = None) -> List[Dict]:
        """Retorna alertas gerados, opcionalmente filtrados por tempo."""
        if since_timestamp:
            return [a for a in self._alerts if a["timestamp"] >= since_timestamp]
        return self._alerts.copy()

    def _generate_alert_seal(self, stream: CoherenceStream) -> str:
        payload = {
            "event": "phi_c_alert",
            "cell_id": stream.cell_id,
            "phi_c": stream.phi_c_estimate,
            "timestamp": stream.timestamp,
            "canon": "∞.Ω.∇+++.329.realtime_monitor"
        }
        return hashlib.sha3_256(
            json.dumps(payload, sort_keys=True).encode()
        ).hexdigest()
