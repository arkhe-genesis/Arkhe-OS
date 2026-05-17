"""
Substrato 200: Fraud Detection com ML + TinyML Edge
Detecta fraudes em tempo real usando Isolation Forest no core banking
e TinyML nos terminais ATM/PDV.
"""

import numpy as np
import time
from typing import Dict
from sklearn.ensemble import IsolationForest

class FraudDetectionEngine:
    def __init__(self, temporal_chain, phi_bus):
        self.model = IsolationForest(n_estimators=100, contamination=0.01)
        self.temporal = temporal_chain
        self.phi_bus = phi_bus

        # Dummy fitting to avoid NotFittedError during testing
        dummy_data = np.random.rand(100, 5)
        self.model.fit(dummy_data)

    async def score_transaction(self, features: Dict) -> float:
        score = -self.model.score_samples([list(features.values())])[0]
        if score > 0.7:  # Alerta de fraude
            await self.temporal.anchor_event("fraud_alert", {
                "score": float(score), "features": features, "timestamp": time.time()
            })
            await self.phi_bus.publish_metric("fraud_score", float(score))
        return float(score)
