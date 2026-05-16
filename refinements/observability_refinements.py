#!/usr/bin/env python3
"""Observabilidade – Prometheus, tracing, alertas de coerência – Substrato 199.5"""

import asyncio, logging, time, random, hashlib
from collections import deque
from typing import Dict, List, Optional
import numpy as np

logger = logging.getLogger(__name__)

class PrometheusExporter:
    """
    Exporta métricas Φ_C e outras para Prometheus/Grafana.
    Utiliza formato OpenMetrics.
    """
    def __init__(self, push_gateway_url: str = None):
        self.url = push_gateway_url
        self.metrics = {}

    def record_phi_c(self, service: str, phi_c: float):
        self.metrics[f"arkhe_phi_c{{service=\"{service}\"}}"] = phi_c

    def record_throughput(self, component: str, val: float):
        self.metrics[f"arkhe_throughput{{component=\"{component}\"}}"] = val

    async def push(self):
        """Envia métricas para Pushgateway (mockado)."""
        logger.info(f"📡 Exportando métricas para Prometheus: {len(self.metrics)} métricas")
        # Em produção: aiohttp post para pushgateway

class DistributedTracing:
    """
    Tracing distribuído com contexto Arkhe (injetado em headers).
    Permite rastrear uma requisição através de todos os módulos.
    """
    def __init__(self, phi_bus=None):
        self.phi_bus = phi_bus
        self.traces = {}

    def start_span(self, trace_id: str, span_name: str, parent_span: str = None) -> str:
        span_id = hashlib.sha3_256(f"{trace_id}:{span_name}:{time.time()}".encode()).hexdigest()[:12]
        self.traces[span_id] = {"trace_id": trace_id, "parent": parent_span, "name": span_name, "start": time.time()}
        return span_id

    def end_span(self, span_id: str):
        if span_id in self.traces:
            self.traces[span_id]["duration_ms"] = (time.time() - self.traces[span_id]["start"]) * 1000

    def inject_context(self, headers: Dict, trace_id: str):
        headers["X-Arkhe-Trace-Id"] = trace_id

class CoherenceDegradationAlerter:
    """
    Alertas proativos baseados em degradação de coerência (Φ_C).
    Se Φ_C de um módulo cair abaixo de limiar, gera alerta antes do colapso.
    """
    def __init__(self, phi_bus=None, degradation_threshold: float = 0.85):
        self.phi_bus = phi_bus
        self.threshold = degradation_threshold
        self.history = deque(maxlen=100)

    async def monitor_module(self, module_name: str, phi_c: float):
        """Avalia tendência de Φ_C e dispara alerta se necessário."""
        self.history.append((module_name, phi_c, time.time()))
        # Se média das últimas 10 medições cair abaixo do threshold
        if len(self.history) >= 10:
            recent = [p[1] for p in list(self.history)[-10:]]
            avg_phi = np.mean(recent)
            if avg_phi < self.threshold:
                logger.error(f"🚨 Degradação de coerência em {module_name}: Φ_C médio {avg_phi:.3f}")
                if self.phi_bus:
                    await self.phi_bus.publish_metric("coherence_degradation_alert", {
                        "module": module_name, "avg_phi_c": avg_phi
                    })
