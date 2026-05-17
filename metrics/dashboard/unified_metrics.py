#!/usr/bin/env python3
"""
ARKHE OS Unified Metrics Dashboard
Φ_C trends, DP ε usage, compliance status em tempo real.
"""
import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import numpy as np
import logging

logger = logging.getLogger(__name__)

@dataclass
class MetricPoint:
    """Ponto de métrica temporal."""
    timestamp: float
    value: float
    metadata: Dict = field(default_factory=dict)

class UnifiedMetricsDashboard:
    """
    Dashboard unificado para métricas da Catedral.

    Métricas suportadas:
    • Φ_C trends por substrato e por tempo
    • DP ε usage por workflow e por framework
    • Compliance status em tempo real com alertas
    • Resource utilization (CPU, memory, GPU)
    • Security events aggregated
    """

    # Configurações de alertas
    ALERT_THRESHOLDS = {
        "phi_c_critical": 0.9999,
        "phi_c_warning": 0.99995,
        "dp_epsilon_max": 5.0,
        "compliance_coverage_min": 80.0,
        "error_rate_max": 0.01,
    }

    def __init__(
        self,
        temporal_chain=None,
        phi_bus=None,
        retention_hours: int = 168  # 7 dias
    ):
        self.temporal = temporal_chain
        self.phi_bus = phi_bus
        self.retention_seconds = retention_hours * 3600

        # Armazenamento de séries temporais
        self._metrics: Dict[str, List[MetricPoint]] = {
            "phi_c_global": [],
            "phi_c_by_substrate": {},
            "dp_epsilon_by_workflow": {},
            "compliance_by_framework": {},
            "error_rate": [],
            "resource_utilization": [],
        }

        # Cache de alertas para evitar spam
        self._alert_cooldown: Dict[str, float] = {}
        self._alert_cooldown_seconds = 300  # 5 minutos entre alertas do mesmo tipo

    async def record_metric(
        self,
        metric_name: str,
        value: float,
        metadata: Optional[Dict] = None,
        substrate: Optional[str] = None,
        workflow: Optional[str] = None,
        framework: Optional[str] = None
    ):
        """
        Registra ponto de métrica no dashboard.

        Args:
            metric_name: Nome da métrica (ex: "phi_c", "dp_epsilon", "compliance_coverage")
            value: Valor numérico da métrica
            metadata: Metadados adicionais
            substrate: ID do substrato (para métricas por-substrato)
            workflow: Nome do workflow (para métricas por-workflow)
            framework: Framework regulatório (para métricas de compliance)
        """
        timestamp = time.time()
        point = MetricPoint(timestamp=timestamp, value=value, metadata=metadata or {})

        # Armazenar na série temporal apropriada
        if metric_name == "phi_c" and substrate:
            key = f"phi_c_by_substrate:{substrate}"
            if key not in self._metrics:
                self._metrics[key] = []
            self._metrics[key].append(point)

        elif metric_name == "dp_epsilon" and workflow:
            key = f"dp_epsilon_by_workflow:{workflow}"
            if key not in self._metrics:
                self._metrics[key] = []
            self._metrics[key].append(point)

        elif metric_name == "compliance_coverage" and framework:
            key = f"compliance_by_framework:{framework}"
            if key not in self._metrics:
                self._metrics[key] = []
            self._metrics[key].append(point)

        elif metric_name in self._metrics:
            self._metrics[metric_name].append(point)

        # Limpar dados antigos (retenção)
        cutoff = timestamp - self.retention_seconds
        for key in self._metrics:
            if isinstance(self._metrics[key], list):
                self._metrics[key] = [
                    p for p in self._metrics[key] if p.timestamp > cutoff
                ]

        # Verificar thresholds e gerar alertas se necessário
        await self._check_alerts(metric_name, value, metadata, substrate, workflow, framework)

        # Publicar no Phi-Bus se disponível
        if self.phi_bus:
            await self.phi_bus.publish_metric("dashboard_metric_recorded", {
                "metric": metric_name,
                "value": value,
                "timestamp": timestamp,
                **({"substrate": substrate} if substrate else {}),
                **({"workflow": workflow} if workflow else {}),
                **({"framework": framework} if framework else {}),
            })

    async def _check_alerts(
        self,
        metric_name: str,
        value: float,
        metadata: Dict,
        substrate: Optional[str],
        workflow: Optional[str],
        framework: Optional[str]
    ):
        """Verifica thresholds e gera alertas se necessário."""
        alert_key = f"{metric_name}:{substrate or workflow or framework or 'global'}"

        # Verificar cooldown para evitar spam
        if alert_key in self._alert_cooldown:
            if time.time() - self._alert_cooldown[alert_key] < self._alert_cooldown_seconds:
                return

        triggered = False
        alert_message = None

        # Verificar thresholds por tipo de métrica
        if metric_name == "phi_c":
            if value < self.ALERT_THRESHOLDS["phi_c_critical"]:
                triggered = True
                alert_message = f"🚨 Φ_C CRÍTICO: {value:.6f} < {self.ALERT_THRESHOLDS['phi_c_critical']}"
            elif value < self.ALERT_THRESHOLDS["phi_c_warning"]:
                triggered = True
                alert_message = f"⚠️  Φ_C BAIXO: {value:.6f} < {self.ALERT_THRESHOLDS['phi_c_warning']}"

        elif metric_name == "dp_epsilon":
            if value > self.ALERT_THRESHOLDS["dp_epsilon_max"]:
                triggered = True
                alert_message = f"⚠️  DP ε ALTO: {value:.2f} > {self.ALERT_THRESHOLDS['dp_epsilon_max']}"

        elif metric_name == "compliance_coverage":
            if value < self.ALERT_THRESHOLDS["compliance_coverage_min"]:
                triggered = True
                alert_message = f"⚠️  COBERTURA INSUFICIENTE: {value:.1f}% < {self.ALERT_THRESHOLDS['compliance_coverage_min']}%"

        if triggered:
            # Registrar cooldown
            self._alert_cooldown[alert_key] = time.time()

            # Preparar payload do alerta
            alert_payload = {
                "alert_type": metric_name,
                "severity": "critical" if "CRÍTICO" in alert_message else "warning",
                "message": alert_message,
                "value": value,
                "threshold": self.ALERT_THRESHOLDS.get(f"{metric_name}_critical") or self.ALERT_THRESHOLDS.get(f"{metric_name}_warning"),
                "timestamp": time.time(),
                **({"substrate": substrate} if substrate else {}),
                **({"workflow": workflow} if workflow else {}),
                **({"framework": framework} if framework else {}),
                "metadata": metadata,
            }

            # Ancorar alerta na TemporalChain
            if self.temporal:
                seal = await self.temporal.anchor_event("dashboard_alert_triggered", alert_payload)
                alert_payload["temporal_seal"] = seal

            # Logar alerta
            logger.warning(f"🚨 ALERT: {alert_message} | Seal: {alert_payload.get('temporal_seal', 'N/A')[:16] if alert_payload.get('temporal_seal') else 'N/A'}")

            # Em produção: enviar para Slack/PagerDuty/etc.
            # await self._send_external_alert(alert_payload)

    def get_dashboard_data(
        self,
        time_range_hours: int = 24,
        granularity_minutes: int = 15
    ) -> Dict:
        """
        Retorna dados para renderização do dashboard.

        Args:
            time_range_hours: Janela temporal para consultar
            granularity_minutes: Granularidade de agregação

        Returns:
            Dict com dados estruturados para frontend
        """
        cutoff = time.time() - (time_range_hours * 3600)
        interval_seconds = granularity_minutes * 60

        dashboard = {
            "generated_at": datetime.utcnow().isoformat(),
            "time_range_hours": time_range_hours,
            "granularity_minutes": granularity_minutes,
            "alerts": self._get_recent_alerts(time_range_hours),
            "charts": {},
            "summary": {},
        }

        # Φ_C Global Trend
        if "phi_c_global" in self._metrics:
            dashboard["charts"]["phi_c_global"] = self._aggregate_series(
                self._metrics["phi_c_global"], cutoff, interval_seconds
            )

        # Φ_C por Substrato
        substrate_charts = {}
        for key, series in self._metrics.items():
            if key.startswith("phi_c_by_substrate:"):
                substrate = key.split(":", 1)[1]
                substrate_charts[substrate] = self._aggregate_series(series, cutoff, interval_seconds)
        if substrate_charts:
            dashboard["charts"]["phi_c_by_substrate"] = substrate_charts

        # DP ε por Workflow
        dp_charts = {}
        for key, series in self._metrics.items():
            if key.startswith("dp_epsilon_by_workflow:"):
                workflow = key.split(":", 1)[1]
                dp_charts[workflow] = self._aggregate_series(series, cutoff, interval_seconds)
        if dp_charts:
            dashboard["charts"]["dp_epsilon_by_workflow"] = dp_charts

        # Compliance por Framework
        compliance_data = {}
        for key, series in self._metrics.items():
            if key.startswith("compliance_by_framework:"):
                framework = key.split(":", 1)[1]
                latest = [p for p in series if p.timestamp > cutoff]
                if latest:
                    compliance_data[framework] = {
                        "current_coverage": latest[-1].value,
                        "trend": self._calculate_trend(latest, interval_seconds),
                        "status": "compliant" if latest[-1].value >= 80 else "non_compliant",
                    }
        if compliance_data:
            dashboard["summary"]["compliance_by_framework"] = compliance_data

        # Summary Statistics
        dashboard["summary"]["global_phi_c"] = {
            "current": self._get_latest("phi_c_global"),
            "avg_24h": self._get_average("phi_c_global", cutoff),
            "min_24h": self._get_minimum("phi_c_global", cutoff),
        }

        return dashboard

    def _aggregate_series(
        self,
        series: List[MetricPoint],
        cutoff: float,
        interval_seconds: int
    ) -> List[Dict]:
        """Agrega série temporal em intervalos regulares."""
        if not series:
            return []

        # Filtrar por cutoff
        filtered = [p for p in series if p.timestamp > cutoff]
        if not filtered:
            return []

        # Agrupar por intervalo
        aggregated = []
        current_interval_start = int(filtered[0].timestamp // interval_seconds) * interval_seconds

        interval_values = []
        for point in filtered:
            point_interval = int(point.timestamp // interval_seconds) * interval_seconds

            if point_interval != current_interval_start:
                # Fechar intervalo anterior
                if interval_values:
                    aggregated.append({
                        "timestamp": current_interval_start,
                        "value": np.mean(interval_values),
                        "count": len(interval_values),
                    })
                # Iniciar novo intervalo
                current_interval_start = point_interval
                interval_values = []

            interval_values.append(point.value)

        # Fechar último intervalo
        if interval_values:
            aggregated.append({
                "timestamp": current_interval_start,
                "value": np.mean(interval_values),
                "count": len(interval_values),
            })

        return aggregated

    def _get_latest(self, metric_key: str) -> Optional[float]:
        """Retorna valor mais recente de uma métrica."""
        if metric_key not in self._metrics or not self._metrics[metric_key]:
            return None
        return self._metrics[metric_key][-1].value

    def _get_average(self, metric_key: str, cutoff: float) -> Optional[float]:
        """Calcula média de uma métrica em janela temporal."""
        if metric_key not in self._metrics:
            return None
        values = [p.value for p in self._metrics[metric_key] if p.timestamp > cutoff]
        return np.mean(values) if values else None

    def _get_minimum(self, metric_key: str, cutoff: float) -> Optional[float]:
        """Calcula mínimo de uma métrica em janela temporal."""
        if metric_key not in self._metrics:
            return None
        values = [p.value for p in self._metrics[metric_key] if p.timestamp > cutoff]
        return np.min(values) if values else None

    def _calculate_trend(self, series: List[MetricPoint], interval_seconds: int) -> str:
        """Calcula tendência (rising/falling/stable) de uma série."""
        if len(series) < 2:
            return "insufficient_data"

        # Comparar primeira e última metade
        mid = len(series) // 2
        first_half_avg = np.mean([p.value for p in series[:mid]])
        second_half_avg = np.mean([p.value for p in series[mid:]])

        change_pct = (second_half_avg - first_half_avg) / first_half_avg * 100

        if abs(change_pct) < 1:
            return "stable"
        elif change_pct > 0:
            return "rising"
        else:
            return "falling"

    def _get_recent_alerts(self, time_range_hours: int) -> List[Dict]:
        """Retorna alertas recentes para exibição no dashboard."""
        # Em produção: consultar TemporalChain ou banco de alertas
        # Mock: retornar alertas simulados baseados em métricas atuais
        alerts = []

        # Verificar Φ_C global
        current_phi = self._get_latest("phi_c_global")
        if current_phi and current_phi < self.ALERT_THRESHOLDS["phi_c_warning"]:
            alerts.append({
                "severity": "critical" if current_phi < self.ALERT_THRESHOLDS["phi_c_critical"] else "warning",
                "metric": "phi_c_global",
                "message": f"Φ_C global abaixo do threshold: {current_phi:.6f}",
                "timestamp": time.time(),
            })

        return alerts
