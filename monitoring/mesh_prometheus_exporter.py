#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mesh_prometheus_exporter.py — Exportador de Métricas Prometheus
Expõe as métricas de coerência, conexões ativas e status do Guardian para o Prometheus/Grafana.
"""

import time
import random
import threading
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class MockPrometheusGauge:
    def __init__(self, name: str, desc: str):
        self.name = name
        self.desc = desc
        self.value = 0.0

    def set(self, val: float):
        self.value = val

class MockPrometheusCounter:
    def __init__(self, name: str, desc: str):
        self.name = name
        self.desc = desc
        self.value = 0.0

    def inc(self, amount: float = 1.0):
        self.value += amount

class MeshPrometheusExporter:
    """Exportador simulado de métricas para a malha Arkhe-Mesh."""

    def __init__(self):
        self.metrics: Dict[str, object] = {
            "arkhe_mesh_streams_active": MockPrometheusGauge("arkhe_mesh_streams_active", "Número de streams ativos por plataforma"),
            "arkhe_mesh_viewers_total": MockPrometheusGauge("arkhe_mesh_viewers_total", "Total de espectadores na malha"),
            "arkhe_mesh_phi_c": MockPrometheusGauge("arkhe_mesh_phi_c", "Coerência Φ_C média da malha"),
            "arkhe_chat_messages_total": MockPrometheusCounter("arkhe_chat_messages_total", "Total de mensagens processadas"),
            "arkhe_chat_guardian_blocks_total": MockPrometheusCounter("arkhe_chat_guardian_blocks_total", "Mensagens bloqueadas pelo Guardian"),
            "arkhe_spark_batch_duration_seconds": MockPrometheusGauge("arkhe_spark_batch_duration_seconds", "Duração de cada batch Spark"),
            "arkhe_temporal_anchors_total": MockPrometheusCounter("arkhe_temporal_anchors_total", "Total de eventos ancorados")
        }
        self.active = False

    def start_server(self, port: int = 8000):
        self.active = True
        logger.info(f"[Prometheus] Exportador iniciado na porta {port}. Métricas expostas.")

    def update_metrics(self, streams: int, viewers: int, phi_c: float,
                       msg_count: int, blocks: int, batch_dur: float, anchors: int):
        """Atualiza as métricas no exportador."""
        self.metrics["arkhe_mesh_streams_active"].set(streams)
        self.metrics["arkhe_mesh_viewers_total"].set(viewers)
        self.metrics["arkhe_mesh_phi_c"].set(phi_c)
        self.metrics["arkhe_chat_messages_total"].inc(msg_count)
        self.metrics["arkhe_chat_guardian_blocks_total"].inc(blocks)
        self.metrics["arkhe_spark_batch_duration_seconds"].set(batch_dur)
        self.metrics["arkhe_temporal_anchors_total"].inc(anchors)

        self._check_alerts(phi_c, blocks, batch_dur)

    def _check_alerts(self, phi_c: float, blocks: int, batch_dur: float):
        if phi_c < 0.95:
            logger.error(f"[Alertmanager] CRITICAL P1: arkhe_mesh_phi_c caiu para {phi_c:.4f}!")
        if blocks > 100:
            logger.warning(f"[Alertmanager] WARNING P2: arkhe_chat_guardian_blocks_total alto: {blocks} blocks/min.")
        if batch_dur > 30.0:
            logger.warning(f"[Alertmanager] WARNING P2: arkhe_spark_batch_duration_seconds excedeu limite: {batch_dur:.1f}s.")
