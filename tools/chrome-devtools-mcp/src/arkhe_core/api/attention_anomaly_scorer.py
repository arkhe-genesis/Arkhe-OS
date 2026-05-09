import numpy as np
import logging
from typing import Dict, List, Any
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

class AttentionAnomalyScorer:
    """
    Detector de Anomalias de Atenção para o Arkhe.
    Utiliza uma lógica simplificada de GMM/DBSCAN para identificar picos de interesse
    em regiões não-conformes da infraestrutura.
    """
    def __init__(self):
        # Cache simples para simular agregação temporal
        self.attention_history: Dict[str, List[Dict[str, Any]]] = {}
        # Baselines de conformidade (simulados)
        self.node_risk_baseline = {
            "arkhe:Cognitive": 0.8, # Alta criticidade
            "arkhe:Core": 0.2,
            "arkhe:Sensory": 0.3,
            "arkhe:Metabolic": 0.6,
            "arkhe:Immune": 0.1
        }

    def record_interaction(self, session_id: str, uri_hash: str):
        if uri_hash not in self.attention_history:
            self.attention_history[uri_hash] = []

        self.attention_history[uri_hash].append({
            "session_id": session_id,
            "timestamp": datetime.now()
        })

        # Prune old records (> 1 hour)
        cutoff = datetime.now() - timedelta(hours=1)
        self.attention_history[uri_hash] = [
            r for r in self.attention_history[uri_hash] if r["timestamp"] > cutoff
        ]

    def calculate_anomaly_score(self, uri_hash: str, internal_uri: str) -> float:
        interactions = self.attention_history.get(uri_hash, [])
        if not interactions:
            return 0.0

        unique_sessions = len(set(r["session_id"] for r in interactions))

        # Lógica de Convergência: Se múltiplos analistas focam no mesmo nó
        # e o nó tem um risco formal alto, o score de anomalia sobe.
        base_risk = self.node_risk_baseline.get(internal_uri, 0.5)

        # Simulação de Log-Likelihood negativa
        # Quanto mais sessões únicas em um curto espaço de tempo, maior a anomalia
        convergence_factor = np.log1p(unique_sessions) / np.log1p(10)

        anomaly_score = convergence_factor * base_risk

        if anomaly_score > 0.8:
            logger.warning(f"CRITICAL ATTENTION ANOMALY DETECTED on {uri_hash} (URI: {internal_uri})")
            # In production: push to Kafka

        return float(anomaly_score)

    def get_heatmap_signal(self) -> Dict[str, float]:
        """Retorna o estado atual do heatmap de atenção para feedback (opcional)"""
        return {h: self.calculate_anomaly_score(h, "unknown") for h in self.attention_history}
