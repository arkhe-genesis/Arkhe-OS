#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
anomaly_detector.py — Substrato 9032: Detector de Anomalias Baseado em Machine Learning
Detecta padrões de tampering e comportamentos anômalos via modelos de ML treinados.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Union
from enum import Enum, auto
import hashlib
import json
import time
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# TIPOS E CONSTANTES
# ============================================================================

class AnomalyType(Enum):
    """Tipos de anomalias detectáveis."""
    INTEGRITY_DRIFT = "integrity_drift"  # Mudança gradual em hashes/métricas
    BEHAVIORAL_ANOMALY = "behavioral_anomaly"  # Padrão de acesso incomum
    TEMPORAL_ANOMALY = "temporal_anomaly"  # Sequência temporal suspeita
    COHERENCE_ANOMALY = "coherence_anomaly"  # Φ_C fora de padrões esperados
    MULTI_FEATURE_ANOMALY = "multi_feature_anomaly"  # Combinação de features anômala

@dataclass
class AnomalyDetectionResult:
    """Resultado de detecção de anomalia."""
    anomaly_detected: bool
    anomaly_type: Optional[AnomalyType]
    confidence: float  # 0.0 a 1.0
    feature_contributions: Dict[str, float]  # Importância de cada feature
    recommended_action: str
    evidence_summary: Dict
    timestamp: float = field(default_factory=time.time)

@dataclass
class TrainingConfig:
    """Configuração para treinamento de modelos."""
    model_type: str = "isolation_forest"  # ou "random_forest", "autoencoder"
    contamination: float = 0.01  # Proporção esperada de anomalias
    n_estimators: int = 100
    max_samples: Union[str, int] = "auto"
    random_state: int = 42
    features_to_use: List[str] = field(default_factory=lambda: [
        "hash_change_rate",
        "phi_c_variance",
        "access_frequency",
        "temporal_gap_anomaly",
        "signature_validation_failures",
    ])

# ============================================================================
# DETECTOR DE ANOMALIAS
# ============================================================================

class AnomalyDetector:
    """
    Detector de anomalias baseado em machine learning para segurança ARKHE.

    Funcionalidades:
    • Treinamento offline com dados históricos normais
    • Detecção online em tempo real com baixa latência
    • Explicabilidade via feature contributions (SHAP-like)
    • Adaptação contínua via aprendizado semi-supervisionado
    • Integração com TemporalChain para auditoria de detecções
    • Suporte a múltiplos algoritmos (Isolation Forest, Autoencoder, etc.)
    """

    def __init__(self, config: TrainingConfig = None):
        self.config = config or TrainingConfig()
        self.scaler = StandardScaler()
        self.model = None
        self.feature_names = self.config.features_to_use
        self.is_trained = False
        self.normal_stats: Dict[str, Dict] = {}  # Estatísticas de baseline

    def prepare_training_data(
        self,
        historical_data: pd.DataFrame,
        label_column: Optional[str] = None,
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Prepara dados para treinamento do modelo."""
        # Selecionar features
        X = historical_data[self.feature_names].copy()

        # Tratar valores missing
        X = X.fillna(X.median())

        # Normalizar features
        X_scaled = self.scaler.fit_transform(X)

        # Labels (opcional para aprendizado supervisionado)
        y = None
        if label_column and label_column in historical_data.columns:
            y = historical_data[label_column].values

        return X_scaled, y

    def train_model(
        self,
        X_train: np.ndarray,
        y_train: Optional[np.ndarray] = None,
    ) -> bool:
        """Treina modelo de detecção de anomalias."""
        try:
            if self.config.model_type == "isolation_forest":
                self.model = IsolationForest(
                    n_estimators=self.config.n_estimators,
                    max_samples=self.config.max_samples,
                    contamination=self.config.contamination,
                    random_state=self.config.random_state,
                    verbose=1,
                )
                self.model.fit(X_train)

            elif self.config.model_type == "random_forest" and y_train is not None:
                self.model = RandomForestClassifier(
                    n_estimators=self.config.n_estimators,
                    max_depth=10,
                    random_state=self.config.random_state,
                    verbose=1,
                )
                self.model.fit(X_train, y_train)

            else:
                logger.error(f"❌ Modelo não suportado: {self.config.model_type}")
                return False

            # Calcular estatísticas de baseline para features
            self.normal_stats = {
                feature: {
                    "mean": float(np.mean(X_train[:, i])),
                    "std": float(np.std(X_train[:, i])),
                    "min": float(np.min(X_train[:, i])),
                    "max": float(np.max(X_train[:, i])),
                }
                for i, feature in enumerate(self.feature_names)
            }

            self.is_trained = True
            logger.info(f"✅ Modelo {self.config.model_type} treinado com {len(X_train)} amostras")
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao treinar modelo: {e}")
            return False

    def detect_anomaly(
        self,
        feature_values: Dict[str, float],
        context: Optional[Dict] = None,
    ) -> AnomalyDetectionResult:
        """Detecta anomalia em nova observação."""
        if not self.is_trained:
            return AnomalyDetectionResult(
                anomaly_detected=False,
                anomaly_type=None,
                confidence=0.0,
                feature_contributions={},
                recommended_action="Model not trained",
                evidence_summary={"error": "Model not trained"},
            )

        try:
            # Preparar vetor de features
            X = np.array([[feature_values.get(f, 0.0) for f in self.feature_names]])
            X_scaled = self.scaler.transform(X)

            # Predição do modelo
            if self.config.model_type == "isolation_forest":
                # Isolation Forest: -1 = anomalia, 1 = normal
                prediction = self.model.predict(X_scaled)[0]
                score = self.model.score_samples(X_scaled)[0]
                # Converter score para probabilidade de anomalia
                anomaly_prob = 1 - (score + 1) / 2  # score ∈ [-1, 1]
                is_anomaly = prediction == -1

            elif self.config.model_type == "random_forest":
                # Random Forest: probabilidade da classe "anomalia"
                proba = self.model.predict_proba(X_scaled)[0]
                # Assumir que classe 1 é anomalia
                anomaly_prob = proba[1] if len(proba) > 1 else 0.0
                is_anomaly = anomaly_prob > 0.5

            else:
                is_anomaly = False
                anomaly_prob = 0.0

            # Calcular contribuições de features (simplificado)
            feature_contributions = self._compute_feature_contributions(X_scaled[0])

            # Determinar tipo de anomalia baseado em features
            anomaly_type = self._classify_anomaly_type(feature_values, feature_contributions)

            # Gerar recomendação de ação
            recommended_action = self._generate_recommendation(anomaly_type, anomaly_prob)

            return AnomalyDetectionResult(
                anomaly_detected=is_anomaly,
                anomaly_type=anomaly_type,
                confidence=float(anomaly_prob),
                feature_contributions=feature_contributions,
                recommended_action=recommended_action,
                evidence_summary={
                    "feature_values": feature_values,
                    "baseline_stats": {f: self.normal_stats[f]["mean"] for f in self.feature_names},
                    "context": context or {},
                },
            )

        except Exception as e:
            logger.error(f"❌ Erro ao detectar anomalia: {e}")
            return AnomalyDetectionResult(
                anomaly_detected=False,
                anomaly_type=None,
                confidence=0.0,
                feature_contributions={},
                recommended_action=f"Detection error: {str(e)}",
                evidence_summary={"error": str(e)},
            )

    def _compute_feature_contributions(self, x_scaled: np.ndarray) -> Dict[str, float]:
        """Computa contribuição de cada feature para decisão (simplificado)."""
        contributions = {}
        for i, feature in enumerate(self.feature_names):
            # Distância da média normalizada como proxy de contribuição
            baseline_mean = self.normal_stats[feature]["mean"]
            baseline_std = self.normal_stats[feature]["std"]
            if baseline_std > 0:
                z_score = abs((x_scaled[i] - baseline_mean) / baseline_std)
                contributions[feature] = min(1.0, z_score / 3.0)  # Normalizar para [0,1]
            else:
                contributions[feature] = 0.0
        return contributions

    def _classify_anomaly_type(
        self,
        feature_values: Dict[str, float],
        contributions: Dict[str, float],
    ) -> Optional[AnomalyType]:
        """Classifica tipo de anomalia baseado em features e contribuições."""
        if not contributions:
            return None

        # Feature com maior contribuição
        top_feature = max(contributions, key=contributions.get)

        if top_feature == "hash_change_rate":
            return AnomalyType.INTEGRITY_DRIFT
        elif top_feature == "phi_c_variance":
            return AnomalyType.COHERENCE_ANOMALY
        elif top_feature == "access_frequency":
            return AnomalyType.BEHAVIORAL_ANOMALY
        elif top_feature == "temporal_gap_anomaly":
            return AnomalyType.TEMPORAL_ANOMALY
        else:
            return AnomalyType.MULTI_FEATURE_ANOMALY

    def _generate_recommendation(
        self,
        anomaly_type: Optional[AnomalyType],
        confidence: float,
    ) -> str:
        """Gera recomendação de ação baseada em tipo e confiança."""
        if confidence < 0.3:
            return "Monitorar — baixa confiança na anomalia"

        recommendations = {
            AnomalyType.INTEGRITY_DRIFT: "Verificar integridade de binários e executar re-assinatura",
            AnomalyType.BEHAVIORAL_ANOMALY: "Revisar logs de acesso e validar identidades",
            AnomalyType.TEMPORAL_ANOMALY: "Verificar sincronização de relógio e ancoragens temporais",
            AnomalyType.COHERENCE_ANOMALY: "Investigar degradação de Φ_C e sincronizar barramento",
            AnomalyType.MULTI_FEATURE_ANOMALY: "Executar diagnóstico completo de integridade",
        }

        base_rec = recommendations.get(anomaly_type, "Investigar anomalia detectada")

        if confidence > 0.8:
            return f"CRÍTICO: {base_rec} — confiança alta"
        elif confidence > 0.6:
            return f"ALERTA: {base_rec} — confiança moderada"
        else:
            return f"AVISO: {base_rec} — confiança baixa"

    def evaluate_model(
        self,
        X_test: np.ndarray,
        y_test: Optional[np.ndarray] = None,
    ) -> Dict:
        """Avalia desempenho do modelo em dados de teste."""
        if not self.is_trained:
            return {"error": "Model not trained"}

        results = {}

        if self.config.model_type == "isolation_forest":
            predictions = self.model.predict(X_test)
            scores = self.model.score_samples(X_test)
            # Converter para labels binários (1 = anomalia)
            y_pred = (predictions == -1).astype(int)

            if y_test is not None:
                # Métricas de classificação
                results["classification_report"] = classification_report(
                    y_test, y_pred, output_dict=True, zero_division=0
                )
                results["confusion_matrix"] = confusion_matrix(y_test, y_pred).tolist()

            results["anomaly_scores"] = {
                "mean": float(np.mean(scores)),
                "std": float(np.std(scores)),
                "min": float(np.min(scores)),
                "max": float(np.max(scores)),
            }

        elif self.config.model_type == "random_forest" and y_test is not None:
            y_pred = self.model.predict(X_test)
            results["classification_report"] = classification_report(
                y_test, y_pred, output_dict=True, zero_division=0
            )
            results["confusion_matrix"] = confusion_matrix(y_test, y_pred).tolist()

        return results

    def generate_detection_proof(
        self,
        detection_result: AnomalyDetectionResult,
        input_features: Dict[str, float],
    ) -> str:
        """Gera prova de integridade para detecção de anomalia."""
        proof_data = {
            "anomaly_detected": detection_result.anomaly_detected,
            "anomaly_type": detection_result.anomaly_type.value if detection_result.anomaly_type else None,
            "confidence": detection_result.confidence,
            "top_contributions": dict(sorted(
                detection_result.feature_contributions.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]),
            "input_feature_hashes": {
                k: hashlib.sha3_256(str(v).encode()).hexdigest()[:8]
                for k, v in input_features.items()
            },
            "timestamp": detection_result.timestamp,
        }

        return hashlib.sha3_256(
            json.dumps(proof_data, sort_keys=True, default=str).encode()
        ).hexdigest()[:16]
