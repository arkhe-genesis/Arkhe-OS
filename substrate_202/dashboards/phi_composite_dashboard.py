#!/usr/bin/env python3
"""
ARKHE OS Substrato 202: Composite Φ_C Monitoring Dashboard
Canon: ∞.Ω.∇+++.202.phi_composite.dashboard
"""

import asyncio
import hashlib
import time
import numpy as np
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from collections import deque
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(message)s')
logger = logging.getLogger(__name__)

class LayerType(Enum):
    MAINFRAME_ACID = "layer_1_mainframe_acid"
    BEAVER_LOGIC = "layer_2_beaver_logic"
    TOKEN_ARKHE_INTENTION = "layer_3_token_arkhe_intention"
    TEMPORALCHAIN_META = "layer_4_temporalchain_meta"

@dataclass
class LayerPhiCMetric:
    layer: LayerType
    phi_c_value: float
    phi_c_trend: float
    consistency_score: float
    latency_ms: float
    error_rate: float
    last_updated: float = field(default_factory=time.time)

    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class CompositePhiCReport:
    report_id: str
    timestamp: float
    layer_metrics: Dict[LayerType, LayerPhiCMetric]
    composite_phi_c: float
    divergence_score: float
    alert_level: str
    recommendations: List[str]
    temporal_seal: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "report_id": self.report_id,
            "timestamp": self.timestamp,
            "layer_metrics": {k.value: v.to_dict() for k, v in self.layer_metrics.items()},
            "composite_phi_c": self.composite_phi_c,
            "divergence_score": self.divergence_score,
            "alert_level": self.alert_level,
            "recommendations": self.recommendations,
            "temporal_seal": self.temporal_seal
        }

class LayerPhiCMonitor:
    ALERT_THRESHOLDS = {
        LayerType.MAINFRAME_ACID: {"min_phi_c": 0.999, "max_latency_ms": 50, "max_error_rate": 0.001},
        LayerType.BEAVER_LOGIC: {"min_phi_c": 0.995, "max_latency_ms": 200, "max_error_rate": 0.01},
        LayerType.TOKEN_ARKHE_INTENTION: {"min_phi_c": 0.95, "max_latency_ms": 1000, "max_error_rate": 0.05},
        LayerType.TEMPORALCHAIN_META: {"min_phi_c": 0.9999, "max_latency_ms": 5000, "max_error_rate": 0.001}
    }

    def __init__(self, layer: LayerType, window_size: int = 100):
        self.layer = layer
        self.window_size = window_size
        self._metrics_history: deque = deque(maxlen=window_size)
        self._current_phi_c = 0.95
        self._trend_window = 10

    def update_metric(self, phi_c_value: float, consistency_score: float, latency_ms: float, error_rate: float) -> LayerPhiCMetric:
        recent_phi_c = [m.phi_c_value for m in list(self._metrics_history)[-self._trend_window:]]
        if len(recent_phi_c) >= 2:
            trend = (recent_phi_c[-1] - recent_phi_c[0]) / len(recent_phi_c)
        else:
            trend = 0.0

        metric = LayerPhiCMetric(
            layer=self.layer,
            phi_c_value=phi_c_value,
            phi_c_trend=trend,
            consistency_score=consistency_score,
            latency_ms=latency_ms,
            error_rate=error_rate
        )

        self._metrics_history.append(metric)
        self._current_phi_c = phi_c_value

        return metric

    def get_current_metric(self) -> LayerPhiCMetric:
        if not self._metrics_history:
            return LayerPhiCMetric(
                layer=self.layer,
                phi_c_value=self._current_phi_c,
                phi_c_trend=0.0,
                consistency_score=0.95,
                latency_ms=100.0,
                error_rate=0.01
            )
        return self._metrics_history[-1]

    def check_alert_thresholds(self, metric: LayerPhiCMetric) -> Tuple[bool, str]:
        thresholds = self.ALERT_THRESHOLDS[self.layer]

        if metric.phi_c_value < thresholds["min_phi_c"]:
            return True, f"phi_c_below_threshold: {metric.phi_c_value:.4f} < {thresholds['min_phi_c']}"
        if metric.latency_ms > thresholds["max_latency_ms"]:
            return True, f"latency_exceeded: {metric.latency_ms:.1f}ms > {thresholds['max_latency_ms']}ms"
        if metric.error_rate > thresholds["max_error_rate"]:
            return True, f"error_rate_exceeded: {metric.error_rate:.3f} > {thresholds['max_error_rate']}"

        return False, "OK"

class CompositePhiCCalculator:
    LAYER_WEIGHTS = {
        LayerType.MAINFRAME_ACID: 0.25,
        LayerType.BEAVER_LOGIC: 0.25,
        LayerType.TOKEN_ARKHE_INTENTION: 0.25,
        LayerType.TEMPORALCHAIN_META: 0.25
    }

    @staticmethod
    def calculate_composite_phi_c(layer_metrics: Dict[LayerType, LayerPhiCMetric]) -> float:
        weighted_sum = sum(
            metric.phi_c_value * CompositePhiCCalculator.LAYER_WEIGHTS[layer]
            for layer, metric in layer_metrics.items()
        )
        return min(1.0, max(0.0, weighted_sum))

    @staticmethod
    def calculate_divergence_score(layer_metrics: Dict[LayerType, LayerPhiCMetric]) -> float:
        if len(layer_metrics) < 2:
            return 0.0

        phi_c_values = [m.phi_c_value for m in layer_metrics.values()]

        std_dev = np.std(phi_c_values)
        mean_phi_c = np.mean(phi_c_values)

        normalized_divergence = min(1.0, std_dev / 0.1 * (1.0 - mean_phi_c))

        return normalized_divergence

    @staticmethod
    def determine_alert_level(composite_phi_c: float, divergence_score: float) -> str:
        if composite_phi_c >= 0.999 and divergence_score <= 0.01:
            return "normal"
        elif composite_phi_c >= 0.99 or divergence_score <= 0.05:
            return "warning"
        else:
            return "critical"

    @staticmethod
    def generate_recommendations(layer_metrics: Dict[LayerType, LayerPhiCMetric], alert_level: str, divergence_score: float) -> List[str]:
        recommendations = []

        if alert_level == "critical":
            recommendations.append("🚨 CRITICAL: Investigar divergência entre camadas imediatamente")
            recommendations.append("🔍 Verificar health checks de todos os componentes do loop")

        for layer, metric in layer_metrics.items():
            if metric.phi_c_value < 0.95:
                recommendations.append(f"⚠️ {layer.value}: Φ_C baixo ({metric.phi_c_value:.3f}) — revisar consistência")
            if metric.error_rate > 0.05:
                recommendations.append(f"⚠️ {layer.value}: Taxa de erros elevada ({metric.error_rate:.2%}) — investigar falhas")
            if metric.latency_ms > 1000:
                recommendations.append(f"⚠️ {layer.value}: Latência alta ({metric.latency_ms:.0f}ms) — otimizar processamento")

        if divergence_score > 0.1:
            recommendations.append("🔄 Divergência entre camadas — sincronizar estados via TemporalChain")
            recommendations.append("📊 Revisar pesos de Φ_C composto se divergência persistir")

        if not recommendations:
            recommendations.append("✅ Sistema operando dentro de parâmetros normais")

        return recommendations

class PhiCCompositeDashboard:
    def __init__(self, temporal_chain=None, phi_bus=None, update_interval_sec: float = 5.0):
        self.temporal = temporal_chain
        self.phi_bus = phi_bus
        self.update_interval = update_interval_sec

        self.layer_monitors = {
            layer: LayerPhiCMonitor(layer)
            for layer in LayerType
        }

        self.calculator = CompositePhiCCalculator()
        self._report_history: deque = deque(maxlen=1000)
        self._running = False

    async def _generate_and_publish_report(self):
        layer_metrics = {
            layer: monitor.get_current_metric()
            for layer, monitor in self.layer_monitors.items()
        }

        composite_phi_c = self.calculator.calculate_composite_phi_c(layer_metrics)
        divergence_score = self.calculator.calculate_divergence_score(layer_metrics)
        alert_level = self.calculator.determine_alert_level(composite_phi_c, divergence_score)
        recommendations = self.calculator.generate_recommendations(layer_metrics, alert_level, divergence_score)

        report_id = hashlib.sha3_256(
            f"{composite_phi_c}:{divergence_score}:{time.time()}".encode()
        ).hexdigest()[:12]

        report = CompositePhiCReport(
            report_id=report_id,
            timestamp=time.time(),
            layer_metrics=layer_metrics,
            composite_phi_c=composite_phi_c,
            divergence_score=divergence_score,
            alert_level=alert_level,
            recommendations=recommendations
        )

        if self.temporal and alert_level != "normal":
            pass # mock

        if self.phi_bus:
            pass # mock

        self._report_history.append(report)

        if alert_level != "normal":
            logger.warning(
                f"📊 Φ_C Composite Report: {report_id} | "
                f"Φ_C={composite_phi_c:.5f} | "
                f"Divergência={divergence_score:.3f} | "
                f"Alerta: {alert_level.upper()}"
            )

        return report

    def simulate_layer_update(self, layer: LayerType, phi_c_value: float, consistency_score: float, latency_ms: float, error_rate: float):
        monitor = self.layer_monitors[layer]
        metric = monitor.update_metric(phi_c_value, consistency_score, latency_ms, error_rate)

        alert_triggered, alert_reason = monitor.check_alert_thresholds(metric)
        if alert_triggered:
            logger.warning(f"⚠️ Alerta {layer.value}: {alert_reason}")

        return metric

    def get_current_dashboard_state(self) -> Dict:
        layer_metrics = {
            layer.value: monitor.get_current_metric().to_dict()
            for layer, monitor in self.layer_monitors.items()
        }

        composite_phi_c = self.calculator.calculate_composite_phi_c(
            {layer: monitor.get_current_metric() for layer, monitor in self.layer_monitors.items()}
        )
        divergence_score = self.calculator.calculate_divergence_score(
            {layer: monitor.get_current_metric() for layer, monitor in self.layer_monitors.items()}
        )

        return {
            "timestamp": time.time(),
            "layer_metrics": layer_metrics,
            "composite_phi_c": composite_phi_c,
            "divergence_score": divergence_score,
            "alert_level": self.calculator.determine_alert_level(composite_phi_c, divergence_score),
            "recent_reports": [
                {"report_id": r.report_id, "composite_phi_c": r.composite_phi_c, "alert_level": r.alert_level}
                for r in list(self._report_history)[-10:]
            ]
        }
