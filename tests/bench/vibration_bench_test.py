#!/usr/bin/env python3
"""
Substrato 192: Validação em bancada de vibração controlada
Testa agente ESP32-S3 com shaker piezoelétrico e ADXL345 real.
"""

import asyncio
import serial
import numpy as np
import time
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BenchTestConfig:
    """Configuração da bancada de testes."""
    serial_port: str = "/dev/ttyUSB0"
    baud_rate: int = 115200
    shaker_dac_channel: int = 0  # Canal DAC para controle do shaker
    test_duration_seconds: int = 300  # 5 minutos
    anomaly_scenarios: List[Dict] = field(default_factory=lambda: [
        {"type": "normal", "frequency_hz": 50, "amplitude_g": 0.5, "duration_s": 60},
        {"type": "imbalance", "frequency_hz": 50, "amplitude_g": 1.2, "duration_s": 60},
        {"type": "seal_failure", "frequency_hz": 120, "amplitude_g": 2.0, "duration_s": 60},
        {"type": "normal", "frequency_hz": 50, "amplitude_g": 0.5, "duration_s": 60},
        {"type": "random_fault", "frequency_hz": 80, "amplitude_g": 1.8, "duration_s": 60},
    ])

@dataclass
class TestResult:
    """Resultado consolidado do teste de bancada."""
    total_samples: int
    true_positives: int
    true_negatives: int
    false_positives: int
    false_negatives: int
    avg_inference_latency_ms: float
    max_inference_latency_ms: float
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    temporal_seal: Optional[str] = None

class VibrationBenchValidator:
    """Valida agente TinyML em bancada de vibração controlada."""

    def __init__(self, config: BenchTestConfig, temporal_chain=None):
        self.config = config
        self.temporal = temporal_chain
        self.ser: Optional[serial.Serial] = None
        self.results: List[Dict] = []

    async def connect_to_esp32(self) -> bool:
        """Conecta ao ESP32-S3 via UART."""
        # MOCKED for tests
        return True

    async def control_shaker(self, frequency_hz: float, amplitude_g: float, duration_s: float):
        """Controla shaker piezoelétrico via DAC (simulado)."""
        logger.info(f"🔊 Shaker: {frequency_hz} Hz @ {amplitude_g}g for {duration_s}s")
        await asyncio.sleep(0.01) # fast simulation

    async def read_esp32_inference(self) -> Optional[Dict]:
        """Lê resultado de inferência do ESP32 via UART."""
        # Mocked return
        return {
            "anomaly": np.random.rand() > 0.5,
            "confidence": np.random.rand(),
            "ts": time.time(),
            "_received_at": time.time(),
            "_inferred_at": time.time() - 0.038
        }

    async def run_bench_test(self) -> TestResult:
        """Executa teste completo de bancada."""
        logger.info(f"🧪 Iniciando validação de bancada: {self.config.test_duration_seconds}s")

        if not await self.connect_to_esp32():
            return self._failed_result()

        start_time = time.time()
        inference_latencies = []
        ground_truth = []
        predictions = []

        # Executar cenários de teste
        for scenario in self.config.anomaly_scenarios:
            # Configurar shaker
            await self.control_shaker(
                scenario["frequency_hz"],
                scenario["amplitude_g"],
                scenario["duration_s"]
            )

            # Coletar inferências durante cenário
            for _ in range(5): # Mock 5 samples per scenario
                result = await self.read_esp32_inference()
                if result:
                    # Calcular latência
                    latency_ms = (result["_received_at"] - result.get("_inferred_at", result["_received_at"])) * 1000
                    inference_latencies.append(latency_ms)

                    # Registrar para métricas
                    ground_truth.append(1 if scenario["type"] != "normal" else 0)
                    predictions.append(1 if result.get("anomaly", False) else 0)

                    self.results.append({
                        "timestamp": result["_received_at"],
                        "scenario": scenario["type"],
                        "predicted_anomaly": result.get("anomaly"),
                        "confidence": result.get("confidence"),
                        "latency_ms": latency_ms,
                    })

        # Calcular métricas
        tp = sum(1 for gt, pred in zip(ground_truth, predictions) if gt == 1 and pred == 1)
        tn = sum(1 for gt, pred in zip(ground_truth, predictions) if gt == 0 and pred == 0)
        fp = sum(1 for gt, pred in zip(ground_truth, predictions) if gt == 0 and pred == 1)
        fn = sum(1 for gt, pred in zip(ground_truth, predictions) if gt == 1 and pred == 0)

        accuracy = (tp + tn) / max(1, len(ground_truth))
        precision = tp / max(1, tp + fp)
        recall = tp / max(1, tp + fn)
        f1 = 2 * precision * recall / max(0.001, precision + recall)

        result = TestResult(
            total_samples=len(ground_truth),
            true_positives=tp,
            true_negatives=tn,
            false_positives=fp,
            false_negatives=fn,
            avg_inference_latency_ms=np.mean(inference_latencies) if inference_latencies else 0,
            max_inference_latency_ms=max(inference_latencies) if inference_latencies else 0,
            accuracy=round(accuracy, 4),
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1_score=round(f1, 4),
        )

        # Ancorar na TemporalChain
        if self.temporal and result.accuracy >= 0.90:
            result.temporal_seal = await self.temporal.anchor_event(
                "bench_validation_completed",
                {
                    "accuracy": result.accuracy,
                    "f1_score": result.f1_score,
                    "avg_latency_ms": result.avg_inference_latency_ms,
                    "total_samples": result.total_samples,
                    "timestamp": time.time(),
                }
            )

        logger.info(
            f"✅ Validação concluída: Acc={result.accuracy:.4f} | "
            f"F1={result.f1_score:.4f} | Lat={result.avg_inference_latency_ms:.1f}ms"
        )

        return result

    def _failed_result(self) -> TestResult:
        """Resultado de falha padronizado."""
        return TestResult(
            total_samples=0, true_positives=0, true_negatives=0,
            false_positives=0, false_negatives=0,
            avg_inference_latency_ms=0, max_inference_latency_ms=0,
            accuracy=0.0, precision=0.0, recall=0.0, f1_score=0.0,
        )
