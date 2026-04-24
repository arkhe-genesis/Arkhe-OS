# learning_metrics_exporter.py — Exporta métricas de aprendizado para o Prometheus

from prometheus_client import start_http_server, Gauge, Counter, Histogram
import time
import asyncio
import logging
from typing import Any

class LearningMetricsExporter:
    """Exporta métricas de aprendizado e recuperação para o Prometheus."""

    def __init__(self, port: int = 9101):
        # Métricas de performance de modelos
        self.model_f1_score = Gauge(
            'cathedral_model_f1_score',
            'F1-score do modelo preditivo',
            ['model_id', 'metric']
        )
        self.model_mae = Gauge(
            'cathedral_model_mae',
            'Erro absoluto médio (MAE) do modelo',
            ['model_id', 'metric']
        )

        # Métricas de ações de recuperação
        self.recovery_action_success = Counter(
            'cathedral_recovery_action_success',
            'Ações de recuperação bem-sucedidas',
            ['action_type']
        )
        self.recovery_action_executed = Counter(
            'cathedral_recovery_action_executed',
            'Ações de recuperação executadas',
            ['action_type']
        )

        # Métricas de auditoria e compliance
        self.compliance_score = Gauge(
            'cathedral_compliance_rate',
            'Taxa de conformidade das decisões automatizadas',
            ['framework']
        )
        self.active_incidents = Gauge(
            'cathedral_active_regulatory_incidents',
            'Número de incidentes regulatórios ativos'
        )

        self.port = port
        self.running = False

    def start(self):
        start_http_server(self.port)
        self.running = True
        logging.info(f"[METRICS] Prometheus exporter started on port {self.port}")

    def update_model_metrics(self, model_id: str, metric: str, f1: float, mae: float):
        self.model_f1_score.labels(model_id=model_id, metric=metric).set(f1)
        self.model_mae.labels(model_id=model_id, metric=metric).set(mae)

    def log_recovery_execution(self, action_type: str, success: bool):
        self.recovery_action_executed.labels(action_type=action_type).inc()
        if success:
            self.recovery_action_success.labels(action_type=action_type).inc()

    def update_compliance_metrics(self, framework: str, rate: float, incident_count: int):
        self.compliance_score.labels(framework=framework).set(rate)
        self.active_incidents.set(incident_count)
