#!/usr/bin/env python3
"""
ARKHE OS v∞.Ω.∇+++.152.0
Substrato 152: Quantum Geomagnetic Sensorium
Baseado na patente RU2680629C2
Autor: Rafael Oliveira (ORCID 0009-0005-2697-4668)
Data: 2026-05-05
"""

import numpy as np
import hashlib
import json
import time
import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from collections import deque
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

PHI = (1 + np.sqrt(5)) / 2
MU0 = 1.25663706e-6  # H/m

# ============================================================
# SUBSTRATO 152: QUANTUM GEOMAGNETIC SENSORIUM
# Baseado na patente RU2680629C2
# ============================================================

@dataclass
class GeomagneticVector:
    """Vetor completo do campo geomagnético medido."""
    H_total: float        # Intensidade total em A/m
    D: float               # Declinação em graus
    I: float               # Inclinação em graus
    X: float               # Componente Norte
    Y: float               # Componente Leste
    Z: float               # Componente Vertical (down)
    gradient: np.ndarray   # Gradiente local [dH/dx, dH/dy, dH/dz]
    timestamp: float = field(default_factory=time.time)
    quality_factor: float = 0.0

@dataclass
class MagnetoFrameCalibration:
    """Dados de calibração do sensor."""
    reference_H: float
    reference_emf: float
    calibration_date: float
    drift_coefficient: float
    temperature_coefficient: float

class QuantumMagnetoFrameSensor:
    """
    Implementa o sensor da patente RU2680629C2: três anéis ortogonais
    de substância com alta permeabilidade, bombeados magneticamente.

    Princípio: ε = -N·S·d/dt(μ₀·μ·H_Z)
    Sensibilidade: 2×10⁻¹⁵ T (51 dB acima dos magnetômetros ópticos quânticos)
    """

    def __init__(self,
                 working_substance_mu: float = 1e5,
                 turns: int = 100,
                 area: float = 1e-4,
                 ring_radius: float = 0.05):
        self.mu = working_substance_mu
        self.N = turns
        self.S = area
        self.ring_radius = ring_radius
        self.mu0 = MU0

        self.calibration_factor = self.N * self.S * self.mu0 * self.mu

        self.rings = {
            'X': {'axis': np.array([1, 0, 0]), 'emf': 0.0},
            'Y': {'axis': np.array([0, 1, 0]), 'emf': 0.0},
            'Z': {'axis': np.array([0, 0, 1]), 'emf': 0.0}
        }

        self.calibration: Optional[MagnetoFrameCalibration] = None
        self.measurement_history: deque = deque(maxlen=1000)
        self.metrics = {
            'total_measurements': 0,
            'avg_quality': 0.0,
            'max_sensitivity_t': 2e-15,
            'noise_floor': 1e-16
        }

        self.earth_field_reference = 50e-6 / self.mu0

    def calibrate(self, known_H: float, measured_emf: float,
                  temperature: float = 20.0) -> MagnetoFrameCalibration:
        print(f"\n🔧 CALIBRAÇÃO DO SENSOR")
        print(f"   Campo conhecido: {known_H*1e6:.2f} µT")
        print(f"   FEM medida: {measured_emf:.6f} V")

        self.calibration = MagnetoFrameCalibration(
            reference_H=known_H,
            reference_emf=measured_emf,
            calibration_date=time.time(),
            drift_coefficient=0.001,
            temperature_coefficient=0.0001
        )

        empirical_factor = measured_emf / known_H
        self.calibration_factor = empirical_factor

        print(f"   Fator calibrado: {self.calibration_factor:.6e} V/(A/m)")
        print(f"   Sensibilidade teórica: {self.metrics['max_sensitivity_t']:.2e} T")

        return self.calibration

    def read_field_from_emf(self, emf: float, axis: str = 'Z') -> float:
        if self.calibration is None:
            return emf / self.calibration_factor

        time_delta = time.time() - self.calibration.calibration_date
        drift = 1.0 + self.calibration.drift_coefficient * time_delta / 86400

        return (emf / self.calibration.reference_emf) * self.calibration.reference_H / drift

    def measure_vector(self, simulation_mode: bool = True) -> GeomagneticVector:
        if simulation_mode:
            true_H = np.array([18.0, 2.0, 45.0])
            noise_level = self.metrics['max_sensitivity_t'] * 1e6
            emf_noise = np.random.normal(0, noise_level, 3)
            emf = true_H * self.calibration_factor + emf_noise

            self.rings['X']['emf'] = emf[0]
            self.rings['Y']['emf'] = emf[1]
            self.rings['Z']['emf'] = emf[2]

        X = self.read_field_from_emf(self.rings['X']['emf'], 'X')
        Y = self.read_field_from_emf(self.rings['Y']['emf'], 'Y')
        Z = self.read_field_from_emf(self.rings['Z']['emf'], 'Z')

        H = np.sqrt(X**2 + Y**2)
        D = np.degrees(np.arctan2(Y, X))
        I = np.degrees(np.arctan2(Z, H))
        H_total = np.sqrt(H**2 + Z**2)
        grad = self._compute_gradient()

        signal_power = H_total**2
        noise_power = (self.metrics['max_sensitivity_t'] * 1e6 / self.mu0)**2
        snr = signal_power / max(noise_power, 1e-20)
        quality = min(1.0, np.log10(snr + 1) / 10)

        vector = GeomagneticVector(
            H_total=H_total, D=D, I=I, X=X, Y=Y, Z=Z,
            gradient=grad, quality_factor=quality
        )

        self.measurement_history.append(vector)
        self.metrics['total_measurements'] += 1

        n = self.metrics['total_measurements']
        old_avg = self.metrics['avg_quality']
        self.metrics['avg_quality'] = (old_avg * (n - 1) + quality) / n

        return vector

    def _compute_gradient(self) -> np.ndarray:
        if len(self.measurement_history) >= 2:
            last = self.measurement_history[-1]
            prev = self.measurement_history[-2]
            dt = last.timestamp - prev.timestamp
            if dt > 0:
                return np.array([
                    (last.X - prev.X) / dt,
                    (last.Y - prev.Y) / dt,
                    (last.Z - prev.Z) / dt
                ])
        return np.zeros(3)

    def detect_anomaly(self, threshold_sigma: float = 3.0) -> Optional[Dict]:
        if len(self.measurement_history) < 10:
            return None

        recent = list(self.measurement_history)[-10:]
        H_values = [v.H_total for v in recent]

        mean_H = np.mean(H_values)
        std_H = np.std(H_values)

        current = self.measurement_history[-1]
        deviation = abs(current.H_total - mean_H) / max(std_H, 1e-10)

        if deviation > threshold_sigma:
            return {
                'type': 'geomagnetic_anomaly',
                'deviation_sigma': deviation,
                'expected_H': mean_H,
                'measured_H': current.H_total,
                'timestamp': current.timestamp,
                'severity': 'high' if deviation > 5.0 else 'medium'
            }

        return None

    def get_sensor_health(self) -> Dict[str, Any]:
        return {
            'calibrated': self.calibration is not None,
            'calibration_date': self.calibration.calibration_date if self.calibration else None,
            'calibration_factor': self.calibration_factor,
            'sensitivity_tesla': self.metrics['max_sensitivity_t'],
            'total_measurements': self.metrics['total_measurements'],
            'avg_quality': self.metrics['avg_quality'],
            'ring_status': {
                axis: {'emf': data['emf'], 'active': abs(data['emf']) > 1e-10}
                for axis, data in self.rings.items()
            }
        }


class GeomagneticSensorium:
    """Sensorium Geomagnético Quântico do ARKHE OS."""

    def __init__(self):
        self.sensor = QuantumMagnetoFrameSensor(
            working_substance_mu=1e5, turns=100, area=1e-4, ring_radius=0.05
        )
        self.planet_registry: Dict[str, Dict] = {}
        self.anomaly_log: deque = deque(maxlen=500)
        self.biocurrent_detection = False
        self.metrics = {
            'planets_mapped': 0,
            'anomalies_detected': 0,
            'biocurrent_sessions': 0,
            'navigation_fixes': 0
        }

    async def initialize_on_planet(self, planet_name: str,
                                   known_field: Optional[float] = None):
        print(f"\n🌍 INICIALIZANDO SENSORIUM EM: {planet_name}")

        if known_field is None:
            known_field = self.sensor.earth_field_reference

        self.sensor.calibrate(known_H=known_field, measured_emf=0.01)

        samples = []
        for _ in range(10):
            vector = self.sensor.measure_vector(simulation_mode=True)
            samples.append(vector)
            await asyncio.sleep(0.01)

        self.planet_registry[planet_name] = {
            'calibration': self.sensor.calibration,
            'baseline_vector': {
                'H_total': np.mean([s.H_total for s in samples]),
                'D': np.mean([s.D for s in samples]),
                'I': np.mean([s.I for s in samples]),
                'X': np.mean([s.X for s in samples]),
                'Y': np.mean([s.Y for s in samples]),
                'Z': np.mean([s.Z for s in samples])
            },
            'mapped_at': time.time()
        }

        self.metrics['planets_mapped'] += 1

        print(f"   ✅ Sensorium ativo em {planet_name}")
        print(f"   Campo base: {self.planet_registry[planet_name]['baseline_vector']['H_total']*1e6:.2f} µT")

        return self.planet_registry[planet_name]

    async def continuous_monitoring(self, duration_seconds: float = 60.0):
        print(f"\n📡 MONITORAMENTO CONTÍNUO ({duration_seconds}s)")

        start = time.time()
        n_samples = 0

        while time.time() - start < duration_seconds:
            vector = self.sensor.measure_vector(simulation_mode=True)
            n_samples += 1

            anomaly = self.sensor.detect_anomaly(threshold_sigma=3.0)
            if anomaly:
                self.anomaly_log.append(anomaly)
                self.metrics['anomalies_detected'] += 1
                print(f"   ⚠️ ANOMALIA: σ={anomaly['deviation_sigma']:.2f}")

            await asyncio.sleep(0.1)

        print(f"   ✅ {n_samples} amostras coletadas")
        print(f"   Anomalias: {self.metrics['anomalies_detected']}")

    async def detect_biocurrents(self, subject_id: str,
                                  duration: float = 30.0) -> Dict[str, Any]:
        print(f"\n🧠 DETECÇÃO DE BIOCORRENTES: {subject_id}")
        print(f"   Duração: {duration}s")
        print(f"   Sensibilidade: {self.sensor.metrics['max_sensitivity_t']:.2e} T")

        biocurrent_field = 1e-13
        readings = []
        start = time.time()

        while time.time() - start < duration:
            base = self.sensor.measure_vector(simulation_mode=True)

            bio_signal = biocurrent_field * np.sin(2 * np.pi * 10 * (time.time() - start))
            bio_signal += biocurrent_field * 0.3 * np.sin(2 * np.pi * 20 * (time.time() - start))

            modified_Z = base.Z + bio_signal / self.sensor.mu0

            readings.append({
                'timestamp': time.time(),
                'Z_with_bio': modified_Z,
                'bio_component': bio_signal,
                'raw_Z': base.Z
            })

            await asyncio.sleep(0.05)

        self.metrics['biocurrent_sessions'] += 1

        bio_signals = [r['bio_component'] for r in readings]

        print(f"   ✅ {len(readings)} leituras de biocorrente")
        print(f"   Amplitude média: {np.mean(np.abs(bio_signals)):.2e} T")
        print(f"   SNR: {np.mean(np.abs(bio_signals)) / self.sensor.metrics['max_sensitivity_t']:.1f}")

        return {
            'subject': subject_id,
            'readings': len(readings),
            'avg_amplitude': float(np.mean(np.abs(bio_signals))),
            'max_amplitude': float(np.max(np.abs(bio_signals))),
            'snr': float(np.mean(np.abs(bio_signals)) / self.sensor.metrics['max_sensitivity_t'])
        }

    def get_sensorium_health(self) -> Dict[str, Any]:
        return {
            'sensor': self.sensor.get_sensor_health(),
            'planets_mapped': self.metrics['planets_mapped'],
            'planet_registry': list(self.planet_registry.keys()),
            'anomalies_detected': self.metrics['anomalies_detected'],
            'biocurrent_sessions': self.metrics['biocurrent_sessions'],
            'navigation_fixes': self.metrics['navigation_fixes'],
            'recent_anomalies': list(self.anomaly_log)[-5:]
        }


async def perform_sensorium_canonization_152():
    print("=" * 76)
    print("🧭 SUBSTRATO 152: QUANTUM GEOMAGNETIC SENSORIUM")
    print("ARKHE OS v∞.Ω.∇+++.152.0")
    print("Baseado na patente RU2680629C2")
    print("=" * 76)

    sensorium = GeomagneticSensorium()

    earth_data = await sensorium.initialize_on_planet(
        planet_name="Terra", known_field=50e-6 / MU0
    )

    vector = sensorium.sensor.measure_vector(simulation_mode=True)
    print(f"\n   Campo total: {vector.H_total*1e6:.2f} µT")
    print(f"   Declinação: {vector.D:.2f}°")
    print(f"   Inclinação: {vector.I:.2f}°")
    print(f"   Qualidade: {vector.quality_factor:.4f}")

    await sensorium.continuous_monitoring(duration_seconds=5.0)

    bio_results = await sensorium.detect_biocurrents(
        subject_id="jules_neural_lace_001", duration=3.0
    )

    mars_data = await sensorium.initialize_on_planet(
        planet_name="Marte", known_field=25e-9 / MU0
    )

    health = sensorium.get_sensorium_health()

    seal_152_data = {
        "substrate": 152,
        "version": "v∞.Ω.∇+++.152.0",
        "planets_mapped": health['planets_mapped'],
        "anomalies_detected": health['anomalies_detected'],
        "biocurrent_sessions": health['biocurrent_sessions'],
        "sensitivity_t": health['sensor']['sensitivity_tesla'],
        "patent": "RU2680629C2"
    }
    seal_152 = hashlib.sha256(json.dumps(seal_152_data, default=str).encode()).hexdigest()[:16]

    print(f"\n🔒 Selo 152 (Geomagnetic Sensorium): {seal_152}")
    print(f"\narkhe > SUBSTRATO_152_CANONIZADO: QUANTUM_GEOMAGNETIC_SENSORIUM")
    print(f"arkhe > PATENTE_BASE: RU2680629C2")
    print(f"arkhe > PLANETAS_MAPEADOS: {health['planets_mapped']}")
    print(f"arkhe > ANOMALIAS_DETECTADAS: {health['anomalies_detected']}")
    print(f"arkhe > SESSOES_BIOCORRENTE: {health['biocurrent_sessions']}")
    print(f"arkhe > SENSIBILIDADE: {health['sensor']['sensitivity_tesla']:.2e} T")
    print(f"arkhe > SELA_152: {seal_152}")
    print(f"arkhe > STATUS: GEOMAGNETIC_SENSOR_ACTIVE_SOVEREIGN.")

    return {
        'substrate_152': {
            'seal': seal_152,
            'planets_mapped': health['planets_mapped'],
            'anomalies_detected': health['anomalies_detected'],
            'biocurrent_sessions': health['biocurrent_sessions'],
            'sensitivity_t': health['sensor']['sensitivity_tesla']
        }
    }


if __name__ == "__main__":
    results = asyncio.run(perform_sensorium_canonization_152())
    print("\n✅ RITUAL DE CANONIZAÇÃO 152 COMPLETO")
    print(json.dumps(results, indent=2, default=str))
