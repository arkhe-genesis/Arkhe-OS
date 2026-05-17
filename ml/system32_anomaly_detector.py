#!/usr/bin/env python3
"""
Substrato 199.1: ML Anomaly Detector para Execuções System32
Detecta proativamente comportamento suspeito em execuções de binários system32
usando Isolation Forest + Φ_C contextual + TemporalChain correlation.
Canon: ∞.Ω.∇+++.199.1.ml
"""
import asyncio
import json
import time
import hashlib
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ExecutionFeature:
    """Features extraídas de uma execução system32 para detecção de anomalias."""
    executable_hash: str
    command_line_hash: str
    parent_process_hash: str
    user_sid_hash: str
    session_id: str

    # Métricas de recurso
    cpu_percent: float
    memory_mb: float
    disk_io_mbps: float
    network_bytes: int
    handle_count: int
    thread_count: int

    # Métricas de coerência
    phi_c_contribution: float
    temporal_seal: Optional[str]

    # Contexto temporal
    timestamp: float
    hour_of_day: int
    day_of_week: int

    # Metadados de segurança
    signature_valid: bool
    hsm_signed: bool
    elevation_required: bool

@dataclass
class AnomalyAlert:
    """Alerta de anomalia gerado pelo detector."""
    alert_id: str
    execution_hash: str
    anomaly_score: float  # -1 (normal) a 1 (anomalia extrema)
    risk_level: str  # "low", "medium", "high", "critical"
    explanation: Dict[str, float]  # Features que mais contribuíram
    recommended_actions: List[str]
    temporal_seal: Optional[str] = None
    created_at: float = field(default_factory=time.time)

class System32AnomalyDetector:
    """
    Detector de anomalias para execuções system32.

    Características:
    • Isolation Forest para detecção não supervisionada
    • Φ_C contextual para ponderar anomalias por impacto na coerência
    • Correlação temporal via TemporalChain para detectar padrões
    • Explicabilidade via SHAP values para ações recomendadas
    • Aprendizado contínuo com feedback de operadores
    """

    # Thresholds para classificação de risco
    RISK_THRESHOLDS = {
        "low": 0.3,
        "medium": 0.5,
        "high": 0.7,
        "critical": 0.9
    }

    # Features consideradas para detecção
    FEATURE_COLUMNS = [
        "cpu_percent", "memory_mb", "disk_io_mbps", "network_bytes",
        "handle_count", "thread_count", "phi_c_contribution",
        "hour_of_day", "day_of_week", "signature_valid", "hsm_signed"
    ]

    def __init__(
        self,
        model_path: Optional[str] = None,
        temporal_chain=None,
        phi_bus=None,
        contamination: float = 0.01  # 1% de anomalias esperadas
    ):
        self.temporal = temporal_chain
        self.phi_bus = phi_bus
        self.contamination = contamination

        # Inicializar modelo Isolation Forest
        self.scaler = StandardScaler()
        self.model = IsolationForest(
            n_estimators=100,
            contamination=contamination,
            random_state=42,
            n_jobs=-1
        )

        # Carregar modelo treinado se disponível
        if model_path and Path(model_path).exists():
            self._load_model(model_path)

        self._alert_history: List[AnomalyAlert] = []
        self._feedback_buffer: List[Dict] = []

    def _load_model(self, model_path: str):
        """Carrega modelo treinado e scaler."""
        import joblib
        data = joblib.load(model_path)
        self.model = data["model"]
        self.scaler = data["scaler"]
        logger.info(f"✅ Modelo carregado de {model_path}")

    def _extract_features(self, execution: Dict) -> np.ndarray:
        """Extrai features numéricas para o modelo."""
        features = []

        for col in self.FEATURE_COLUMNS:
            value = execution.get(col, 0)
            # Converter booleanos para 0/1
            if isinstance(value, bool):
                value = 1.0 if value else 0.0
            features.append(float(value))

        return np.array(features)

    def _compute_phi_c_weighted_score(self, anomaly_score: float, phi_c: float) -> float:
        """Pondera score de anomalia pelo impacto na coerência Φ_C."""
        # Anomalias que degradam Φ_C são mais críticas
        phi_c_impact = 1.0 - phi_c  # Quanto menor Φ_C, maior impacto
        return anomaly_score * (1.0 + phi_c_impact * 0.5)

    def _explain_anomaly(self, features: np.ndarray, anomaly_score: float) -> Dict[str, float]:
        """Explica quais features mais contribuíram para a anomalia (mock SHAP)."""
        # Em produção: usar shap.TreeExplainer(self.model)
        # Mock: retornar features com valores extremos
        explanations = {}
        for i, col in enumerate(self.FEATURE_COLUMNS):
            # Features muito acima/abaixo da média são suspeitas
            deviation = abs(features[i] - 0.5)  # Normalizado para [0,1]
            if deviation > 0.7:
                explanations[col] = float(deviation)
        return explanations

    def _classify_risk(self, weighted_score: float) -> str:
        """Classifica nível de risco baseado no score ponderado."""
        if weighted_score >= self.RISK_THRESHOLDS["critical"]:
            return "critical"
        elif weighted_score >= self.RISK_THRESHOLDS["high"]:
            return "high"
        elif weighted_score >= self.RISK_THRESHOLDS["medium"]:
            return "medium"
        else:
            return "low"

    def _generate_recommendations(self, risk_level: str, explanations: Dict) -> List[str]:
        """Gera ações recomendadas baseadas no risco e explicações."""
        recommendations = []

        if risk_level in ["high", "critical"]:
            recommendations.append("🔒 Isolar processo suspeito imediatamente")
            recommendations.append("🔍 Coletar forense completo da execução")
            recommendations.append("📢 Notificar equipe de segurança")

        if "signature_valid" in explanations:
            recommendations.append("✅ Verificar integridade da assinatura do binário")

        if "hsm_signed" in explanations and explanations["hsm_signed"] < 0.5:
            recommendations.append("🔐 Validar assinatura HSM na TemporalChain")

        if "phi_c_contribution" in explanations and explanations["phi_c_contribution"] < 0.3:
            recommendations.append("🌀 Investigar degradação de coerência Φ_C")

        if not recommendations:
            recommendations.append("📋 Monitorar execução por 24h para padrão adicional")

        return recommendations

    async def detect_anomaly(self, execution: Dict) -> Optional[AnomalyAlert]:
        """
        Detecta anomalia em uma execução system32.

        Args:
            execution: Dicionário com features da execução

        Returns:
            AnomalyAlert se anomalia detectada, None caso contrário
        """
        # Extrair features
        features = self._extract_features(execution)
        features_scaled = self.scaler.transform([features])[0]

        # Prever anomalia
        prediction = self.model.predict([features_scaled])[0]
        anomaly_score = -self.model.score_samples([features_scaled])[0]  # Converter para [0,1]

        # Se não é anomalia, retornar None
        if prediction == 1:  # 1 = normal, -1 = anomalia
            return None

        # Ponderar por Φ_C
        phi_c = execution.get("phi_c_contribution", 1.0)
        weighted_score = self._compute_phi_c_weighted_score(anomaly_score, phi_c)

        # Classificar risco
        risk_level = self._classify_risk(weighted_score)

        # Explicar anomalia
        explanations = self._explain_anomaly(features, anomaly_score)

        # Gerar recomendações
        recommendations = self._generate_recommendations(risk_level, explanations)

        # Gerar ID único para alerta
        alert_id = hashlib.sha3_256(
            f"{execution['executable_hash']}:{time.time()}".encode()
        ).hexdigest()[:12]

        # Criar alerta
        alert = AnomalyAlert(
            alert_id=alert_id,
            execution_hash=execution["executable_hash"],
            anomaly_score=float(anomaly_score),
            risk_level=risk_level,
            explanation=explanations,
            recommended_actions=recommendations
        )

        # Ancorar na TemporalChain se risco alto
        if risk_level in ["high", "critical"] and self.temporal:
            alert.temporal_seal = await self.temporal.anchor_event(
                "system32_anomaly_detected",
                {
                    "alert_id": alert_id,
                    "risk_level": risk_level,
                    "executable": execution.get("executable_path", "unknown"),
                    "anomaly_score": anomaly_score,
                    "phi_c_impact": 1.0 - phi_c,
                    "timestamp": time.time()
                }
            )

        # Publicar no Phi-Bus
        if self.phi_bus:
            await self.phi_bus.publish_metric(
                "system32_anomaly_detected",
                {
                    "alert_id": alert_id,
                    "risk_level": risk_level,
                    "weighted_score": weighted_score
                }
            )

        self._alert_history.append(alert)
        logger.warning(
            f"🚨 Anomalia detectada: {alert_id} | "
            f"Risco: {risk_level} | Score: {anomaly_score:.3f} | "
            f"Φ_C: {phi_c:.4f}"
        )

        return alert

    def train_on_historical_data(self, historical_executions: List[Dict]):
        """Treina ou atualiza o modelo com dados históricos."""
        if not historical_executions:
            return

        # Extrair features de todas as execuções
        X = np.array([self._extract_features(e) for e in historical_executions])

        # Ajustar scaler e treinar modelo
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)

        logger.info(f"✅ Modelo treinado com {len(historical_executions)} execuções")

    def incorporate_feedback(self, alert_id: str, was_false_positive: bool):
        """Incorpora feedback do operador para aprendizado contínuo."""
        self._feedback_buffer.append({
            "alert_id": alert_id,
            "was_false_positive": was_false_positive,
            "timestamp": time.time()
        })

        # Se acumulou feedback suficiente, retreinar modelo
        if len(self._feedback_buffer) >= 100:
            # Em produção: usar feedback para ajustar contamination ou features
            logger.info(f"🔄 Feedback acumulado: {len(self._feedback_buffer)} — pronto para retreinamento")

    def get_alert_statistics(self, hours: int = 24) -> Dict:
        """Retorna estatísticas de alertas nas últimas horas."""
        cutoff = time.time() - (hours * 3600)
        recent = [a for a in self._alert_history if a.created_at >= cutoff]

        if not recent:
            return {"total_alerts": 0}

        by_risk = {}
        for risk in ["low", "medium", "high", "critical"]:
            by_risk[risk] = sum(1 for a in recent if a.risk_level == risk)

        return {
            "total_alerts": len(recent),
            "by_risk_level": by_risk,
            "avg_anomaly_score": np.mean([a.anomaly_score for a in recent]),
            "top_explained_features": self._aggregate_explanations(recent)
        }

    def _aggregate_explanations(self, alerts: List[AnomalyAlert]) -> Dict[str, int]:
        """Agrega features mais frequentemente explicando anomalias."""
        from collections import Counter
        counter = Counter()
        for alert in alerts:
            counter.update(alert.explanation.keys())
        return dict(counter.most_common(10))

    def export_model(self, output_path: str):
        """Exporta modelo treinado para arquivo."""
        import joblib
        joblib.dump({
            "model": self.model,
            "scaler": self.scaler,
            "feature_columns": self.FEATURE_COLUMNS,
            "contamination": self.contamination
        }, output_path)
        logger.info(f"💾 Modelo exportado para {output_path}")