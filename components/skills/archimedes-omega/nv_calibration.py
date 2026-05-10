#!/usr/bin/env python3
"""
Calibração dos 168 Sensores NV - Protocolo de Consenso Bizantino
Sistema Arkhe-Ω Rio v2.1
"""

import numpy as np
import asyncio
import json
from dataclasses import dataclass
from typing import List, Tuple, Dict
from datetime import datetime, timezone
import hashlib

@dataclass
class NVSensorReading:
    sensor_id: int
    timestamp: float
    lambda_coherence: float  # λ₂ (0-1)
    phase_vector: np.ndarray  # Vetor de fase (169 dimensões)
    temperature: float       # Temperatura do sensor (K)
    magnetic_field: float    # Campo magnético local (T)
    signature: str           # Assinatura ECDSA

class ByzantineConsensus:
    """
    Implementa consenso bizantino para 168 sensores NV
    Tolerância: f = 56 (1/3 de 168)
    """

    def __init__(self, n_sensors=168, f_faulty=56):
        self.n_sensors = n_sensors
        self.f_faulty = f_faulty
        self.quorum = 2 * f_faulty + 1  # 112 sensores (2/3)
        self.sensors = {}
        self.calibration_map = {}

    async def calibrate_sensors(self):
        """
        Protocolo de calibração em 3 fases:
        1. Pre-prepare: Líder propõe valor de referência
        2. Prepare: Sensores validam e broadcast
        3. Commit: Consenso alcançado
        """
        # Fase 1: Definir valor de referência (λ₂ = 0.85)
        reference_lambda = 0.85

        # Fase 2: Coletar leituras de todos os sensores
        readings = await self._collect_readings()

        # Fase 3: Detectar e isolar sensores falhos/bizantinos
        valid_readings, faulty_sensors = self._detect_faults(readings)

        # Fase 4: Alcançar consenso nas leituras válidas
        consensus_lambda = self._reach_consensus(valid_readings)

        # Fase 5: Calibrar sensores individuais
        self.calibration_map = self._calibrate_individuals(
            valid_readings, consensus_lambda
        )

        calibration_data = {
            'timestamp': datetime.now().isoformat(),
            'reference_lambda': reference_lambda,
            'consensus_lambda': consensus_lambda,
            'faulty_sensors': faulty_sensors,
            'calibration_map': self.calibration_map,
            'total_sensors': self.n_sensors,
            'valid_sensors': len(valid_readings),
            'tolerance': self.f_faulty
        }

        return calibration_data

    async def _collect_readings(self) -> List[NVSensorReading]:
        """Simula coleta de leituras dos 168 sensores"""
        readings = []

        for i in range(self.n_sensors):
            # Simula leitura com algum ruído
            base_lambda = 0.85
            noise = np.random.normal(0, 0.02)

            # Alguns sensores são "bizantinos" (dados falsos)
            if i % 30 == 0:  # ~5% de sensores maliciosos
                noise += 0.2  # Desvio grande

            lambda_val = np.clip(base_lambda + noise, 0, 1)

            reading = NVSensorReading(
                sensor_id=i,
                timestamp=datetime.now().timestamp(),
                lambda_coherence=lambda_val,
                phase_vector=np.random.rand(169),  # Simulado
                temperature=77.0 + np.random.normal(0, 0.1),  # 77K ± 0.1
                magnetic_field=4.5e-3 + np.random.normal(0, 1e-4),  # 4.5mT
                signature=f"sig_{i}_{hashlib.sha256(str(i).encode()).hexdigest()[:16]}"
            )
            readings.append(reading)

        return readings

    def _detect_faults(self, readings: List[NVSensorReading]) -> Tuple[List[NVSensorReading], List[int]]:
        """
        Detecta sensores falhos usando estatística robusta (MAD - Median Absolute Deviation)
        """
        lambdas = np.array([r.lambda_coherence for r in readings])
        median = np.median(lambdas)
        mad = np.median(np.abs(lambdas - median))

        # Limite: ±3 MAD (99.7% de confiança)
        threshold = 3 * mad if mad > 0.001 else 0.05

        valid = []
        faulty = []

        for reading in readings:
            deviation = abs(reading.lambda_coherence - median)
            if deviation <= threshold:
                valid.append(reading)
            else:
                faulty.append(reading.sensor_id)

        # Verifica se número de falhos está dentro da tolerância
        if len(faulty) > self.f_faulty:
            raise ValueError(f"Falhas excessivas: {len(faulty)} > {self.f_faulty}")

        return valid, faulty

    def _reach_consensus(self, valid_readings: List[NVSensorReading]) -> float:
        """Alcança consenso usando média ponderada pela confiança"""
        if len(valid_readings) < self.quorum:
            raise ValueError(f"Quorum não atingido: {len(valid_readings)} < {self.quorum}")

        lambdas = np.array([r.lambda_coherence for r in valid_readings])
        weights = np.array([self._compute_weight(r) for r in valid_readings])

        consensus = np.average(lambdas, weights=weights)
        return float(consensus)

    def _compute_weight(self, reading: NVSensorReading) -> float:
        """Computa peso baseado na qualidade do sensor"""
        # Temperatura próxima de 77K = peso maior
        temp_score = 1.0 - abs(reading.temperature - 77.0) / 10.0

        # Campo magnético estável = peso maior
        field_score = 1.0 - abs(reading.magnetic_field - 4.5e-3) / 1e-3

        return float(max(0.1, temp_score * field_score))

    def _calibrate_individuals(self, valid_readings: List[NVSensorReading],
                              consensus: float) -> Dict[int, float]:
        """Calcula fatores de calibração para cada sensor"""
        calibration_map = {}

        for reading in valid_readings:
            # Fator de correção: valor_consensus / valor_lido
            # Em operação normal, leituras serão multiplicadas por este fator
            correction = consensus / reading.lambda_coherence
            calibration_map[reading.sensor_id] = float(correction)

        return calibration_map

class CalibrationProtocol:
    """Protocolo completo de calibração da Cúpula de Coerência"""

    def __init__(self):
        self.consensus = ByzantineConsensus(n_sensors=168, f_faulty=56)
        self.calibration_history = []

    async def run_full_calibration(self):
        """Executa calibração completa com múltiplas rodadas"""
        # Rodada 1: Calibração inicial
        cal1 = await self.consensus.calibrate_sensors()

        # Rodada 2: Verificação (após aquecimento)
        await asyncio.sleep(0.1)  # Simula tempo de aquecimento
        cal2 = await self.consensus.calibrate_sensors()

        # Rodada 3: Validação final
        cal3 = await self.consensus.calibrate_sensors()

        # Consistência entre rodadas
        consistency = self._check_inter_round_consistency([cal1, cal2, cal3])

        final_report = {
            'calibration_rounds': [cal1, cal2, cal3],
            'inter_round_consistency': float(consistency),
            'status': 'APPROVED' if consistency > 0.99 else 'REJECTED',
            'timestamp': datetime.now().isoformat()
        }

        return final_report

    def _check_inter_round_consistency(self, calibrations: List[Dict]) -> float:
        """Verifica consistência entre rodadas de calibração"""
        consensuses = [c['consensus_lambda'] for c in calibrations]
        mean_consensus = np.mean(consensuses)
        std_consensus = np.std(consensuses)

        if mean_consensus == 0: return 0.0
        consistency = 1.0 - (std_consensus / mean_consensus)
        return float(consistency)

if __name__ == "__main__":
    async def main():
        protocol = CalibrationProtocol()
        report = await protocol.run_full_calibration()
        print(f"Status da Calibração: {report['status']}")
        print(f"Consistência: {report['inter_round_consistency']:.6f}")

    asyncio.run(main())
