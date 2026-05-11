#!/usr/bin/env python3
"""
audit/deviation_tracker.py — Detecção e registro de desvios da configuração canônica.
Monitora execuções e alerta para qualquer divergência significativa.
"""
import json
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from collections import deque

@dataclass
class DeviationAlert:
    """Alerta de desvio detectado."""
    alert_id: str
    timestamp: float
    artifact_seal: str
    deviation_type: str  # "config_mismatch", "coherence_drop", "signature_invalid"
    expected_value: str
    observed_value: str
    severity: str  # "low", "medium", "high", "critical"
    auto_mitigated: bool
    notes: str

    def to_dict(self) -> Dict:
        return {k: v for k, v in self.__dict__.items()}

class DeviationTracker:
    """Monitora e registra desvios da configuração canônica."""

    def __init__(self, canonical_config: Dict, alert_threshold: float = 0.1):
        self.canonical_config = canonical_config
        self.alert_threshold = alert_threshold
        self.recent_executions: deque = deque(maxlen=1000)
        self.alerts: List[DeviationAlert] = []

    def check_execution(self,
                       artifact_seal: str,
                       observed_config: Dict,
                       observed_coherence: float) -> Optional[DeviationAlert]:
        """Verifica se uma execução desvia do canônico."""
        deviations = []

        # 1. Verificar configuração
        for key, expected in self.canonical_config.items():
            # Apenas verificar chaves que estão tanto na canonical quanto na observed
            if key in observed_config:
                observed = observed_config[key]
                if self._is_significant_deviation(expected, observed):
                    deviations.append({
                        "type": "config_mismatch",
                        "key": key,
                        "expected": expected,
                        "observed": observed
                    })

        # 2. Verificar coerência
        expected_coh = self.canonical_config.get("min_coherence", 0.7)
        if observed_coherence < expected_coh - self.alert_threshold:
            deviations.append({
                "type": "coherence_drop",
                "expected": f">= {expected_coh}",
                "observed": f"{observed_coherence:.3f}"
            })

        # Gerar alerta se houver desvios significativos
        if deviations:
            severity = self._compute_severity(deviations)
            alert = DeviationAlert(
                alert_id=f"dev_{int(time.time())}_{artifact_seal[:8]}",
                timestamp=time.time(),
                artifact_seal=artifact_seal,
                deviation_type=deviations[0]["type"],
                expected_value=str(deviations[0]["expected"]),
                observed_value=str(deviations[0]["observed"]),
                severity=severity,
                auto_mitigated=self._auto_mitigate(deviations),
                notes=json.dumps(deviations)
            )
            self.alerts.append(alert)
            return alert

        return None

    def _is_significant_deviation(self, expected, observed) -> bool:
        """Determina se uma diferença é significativa."""
        if isinstance(expected, (int, float)) and isinstance(observed, (int, float)):
            return abs(expected - observed) > self.alert_threshold
        return expected != observed

    def _compute_severity(self, deviations: List[Dict]) -> str:
        """Calcula severidade baseada nos desvios."""
        critical_types = {"config_mismatch", "signature_invalid"}
        if any(d["type"] in critical_types for d in deviations):
            return "critical"
        if len(deviations) >= 3:
            return "high"
        if len(deviations) >= 2:
            return "medium"
        return "low"

    def _auto_mitigate(self, deviations: List[Dict]) -> bool:
        """Tenta mitigar automaticamente desvios."""
        # Exemplo: se coerência caiu, tentar fallback para modelo canônico
        if any(d["type"] == "coherence_drop" for d in deviations):
            # Em produção: ativar fallback, notificar operador, etc.
            return True
        return False

    def get_alerts(self,
                  since: Optional[float] = None,
                  severity: Optional[str] = None) -> List[DeviationAlert]:
        """Recupera alertas filtrados."""
        result = self.alerts
        if since:
            result = [a for a in result if a.timestamp >= since]
        if severity:
            result = [a for a in result if a.severity == severity]
        return result
