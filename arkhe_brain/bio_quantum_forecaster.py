"""
Módulo: bio_quantum_forecaster.py
Finalidade: Antecipar colapsos de coerência usando dados do Bio-Link (40Hz)
"""

import numpy as np
from scipy.stats import entropy
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timezone, timezone

class BioQuantumForecaster:
    def __init__(self, threshold=0.995):
        self.coherence_history = []
        self.critical_threshold = threshold
        self.prediction_window = 300 # 5 minutos à frente

    def predict_collapse(self, bio_data: dict, current_lambda: float):
        """
        Calcula o 'Risco de Colapso' (CR).
        Se a entropia biológica subir, a estabilidade quântica cairá em T+delta.
        """
        sync_ratio = bio_data['sync_ratio']
        hrv_samples = bio_data['hrv_samples']

        # O Índice de Estabilidade Biológica (BSI)
        if len(hrv_samples) > 0:
            hrv_entropy = float(entropy(hrv_samples))
        else:
            hrv_entropy = 1.0

        bsi = sync_ratio / (1 + hrv_entropy)

        # Predição Linear-Quântica do próximo estado de λ₂
        predicted_lambda = current_lambda * (0.7 + 0.3 * bsi)

        is_imminent = bool(predicted_lambda < self.critical_threshold)

        return is_imminent, float(predicted_lambda)

class PredictiveCollapseForecaster:
    """
    Utiliza dados do Bio-Link (sincronia cardíaca, ganho de coerência, variabilidade)
    e histórico de λ₂ para antecipar colapsos de coerência com até 30 segundos de antecedência.
    """
    def __init__(self, history_window: int = 50, prediction_horizon: float = 30.0):
        self.history_window = history_window
        self.prediction_horizon = prediction_horizon  # segundos
        self.lambda_history = []
        self.bio_gain_history = []
        self.sync_ratio_history = []
        self.collapse_alerts = []  # registros de alertas emitidos

    def update(self, current_lambda: float, bio_gain: float, sync_ratio: float):
        """Atualiza o histórico com a última leitura"""
        self.lambda_history.append(current_lambda)
        self.bio_gain_history.append(bio_gain)
        self.sync_ratio_history.append(sync_ratio)

        if len(self.lambda_history) > self.history_window:
            self.lambda_history.pop(0)
            self.bio_gain_history.pop(0)
            self.sync_ratio_history.pop(0)

    def predict_collapse_probability(self) -> Tuple[float, Optional[float]]:
        """
        Retorna (probabilidade de colapso nos próximos `prediction_horizon` segundos,
        valor previsto de λ₂ no horizonte).
        """
        if len(self.lambda_history) < 10:
            return 0.0, None

        # 1. Calcula taxa de variação recente de λ₂ (derivada numérica)
        recent_lambdas = self.lambda_history[-10:]
        x = np.arange(len(recent_lambdas))
        slope_lambda = np.polyfit(x, recent_lambdas, 1)[0]

        # 2. Tendência do ganho do Bio-Link
        recent_gains = self.bio_gain_history[-10:]
        slope_gain = np.polyfit(x, recent_gains, 1)[0]

        # 3. Tendência da sincronia populacional
        recent_sync = self.sync_ratio_history[-10:]
        slope_sync = np.polyfit(x, recent_sync, 1)[0]

        # 4. Modelo de risco: combinação linear ponderada
        risk_score = (
            -5.0 * slope_lambda           # λ₂ caindo rapidamente → alto risco
            - 1.0 * slope_gain            # ganho aumentando → reduz risco
            - 2.0 * slope_sync            # sincronia aumentando → reduz risco
            + 0.5 * (1.0 - recent_lambdas[-1])  # nível absoluto baixo aumenta risco
        )

        prob = float(np.clip(risk_score, 0.0, 1.0))
        predicted_lambda = float(recent_lambdas[-1] + slope_lambda * self.prediction_horizon)
        predicted_lambda = float(np.clip(predicted_lambda, 0.5, 1.0))

        if prob > 0.7:
            self.collapse_alerts.append({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'probability': prob,
                'predicted_lambda': predicted_lambda,
                'slope_lambda': float(slope_lambda)
            })

        return prob, predicted_lambda
