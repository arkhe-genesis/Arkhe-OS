#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rlcr/calibrator.py — Reinforcement Learning for Calibrated Reasoning
Implementação do método MIT RLCR para calibração de confiança em LLMs
"""

import json
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import hashlib
import time

@dataclass
class CalibrationMetrics:
    """Métricas de calibração de confiança."""
    ece: float  # Expected Calibration Error
    mce: float  # Maximum Calibration Error
    accuracy: float
    avg_confidence: float
    n_samples: int

    def is_well_calibrated(self, threshold: float = 0.05) -> bool:
        """Verifica se calibração está dentro do limiar (ECE < threshold)."""
        return self.ece < threshold

class RLCRCalibrator:
    """
    Calibrador de confiança baseado em Reinforcement Learning for Calibrated Reasoning (MIT, 2026).
    """

    def __init__(self, model_path: Optional[str] = None,
                 target_ece: float = 0.05):
        self.target_ece = target_ece
        self.calibration_function = self._load_calibration_function(model_path)
        self.history: List[Dict] = []  # Para aprendizado contínuo

    def calibrate(self, raw_score: float, allegation: 'Alegacao',
                  facts: List[Dict]) -> Tuple[float, str]:
        """
        Aplica calibração a score bruto do LLM.
        Retorna: (confiança_calibrada, justificativa)
        """
        features = self._extract_features(allegation, facts, raw_score)
        calibrated = self.calibration_function.predict(features)
        justification = self._generate_justification(features, calibrated)
        self._record_observation(features, raw_score, calibrated)
        return calibrated, justification

    def _extract_features(self, allegation: 'Alegacao', facts: List[Dict],
                          raw_score: float) -> Dict:
        """Extrai features relevantes para calibração."""
        return {
            'raw_score': raw_score,
            'fact_count': len(facts),
            'source_quality': np.mean([f.get('source_quality', 0.5) for f in facts]) if facts else 0.0,
            'source_diversity': len(set(f.get('source_id', '') for f in facts)),
            'contradiction_count': self._count_contradictions(facts),
            'temporal_recency': self._avg_recency(facts),
            'domain_complexity': self._domain_complexity(getattr(allegation, "domain", "geral")),
            'query_ambiguity': self._query_ambiguity(getattr(allegation, "text", "")),
            'evidence_strength': self._evidence_strength(facts),
        }

    def _count_contradictions(self, facts: List[Dict]) -> int:
        contradictions = 0
        claims = [f.get('claim', '').lower() for f in facts if 'claim' in f]
        for i, claim1 in enumerate(claims):
            for claim2 in claims[i+1:]:
                if self._are_contradictory(claim1, claim2):
                    contradictions += 1
        return contradictions

    def _are_contradictory(self, claim1: str, claim2: str) -> bool:
        contradict_pairs = [
            ("causes", "prevents"),
            ("increases", "decreases"),
            ("is", "is not"),
            ("always", "never"),
            ("approved", "rejected"),
        ]
        c1, c2 = claim1.lower(), claim2.lower()
        return any(p1 in c1 and p2 in c2 or p2 in c1 and p1 in c2
                  for p1, p2 in contradict_pairs)

    def _avg_recency(self, facts: List[Dict]) -> float:
        if not facts:
            return 0.5
        timestamps = [f.get('timestamp', 0) for f in facts if 'timestamp' in f]
        if not timestamps:
            return 0.5
        latest = max(timestamps)
        now = time.time()
        age_years = (now - latest) / (365.25 * 24 * 3600)
        return max(0.0, min(1.0, 0.9 ** age_years))

    def _domain_complexity(self, domain: str) -> float:
        complexity_map = {
            "medicina": 0.9,
            "direito": 0.85,
            "ciencia": 0.8,
            "programacao": 0.7,
            "historia": 0.6,
            "geral": 0.5,
        }
        return complexity_map.get(domain, 0.5)

    def _query_ambiguity(self, query: str) -> float:
        ambiguous_words = ["bank", "spring", "light", "right", "left", "current"]
        words = query.lower().split()
        return min(1.0, len([w for w in words if w in ambiguous_words]) / max(1, len(words)))

    def _evidence_strength(self, facts: List[Dict]) -> float:
        if not facts:
            return 0.0
        strengths = [f.get('evidence_strength', 0.5) for f in facts]
        return float(np.mean(strengths))

    def _generate_justification(self, features: Dict, calibrated: float) -> str:
        reasons = []
        if features['fact_count'] < 3:
            reasons.append("poucas fontes")
        if features['contradiction_count'] > 0:
            reasons.append(f"{features['contradiction_count']} contradições")
        if features['source_quality'] < 0.7:
            reasons.append("fontes de baixa qualidade")
        if features['query_ambiguity'] > 0.5:
            reasons.append("query ambígua")
        if features['temporal_recency'] < 0.6:
            reasons.append("fontes desatualizadas")

        if calibrated < 0.5:
            base = "Evidência insuficiente para confiança alta"
        elif calibrated < 0.7:
            base = "Confiança moderada — evidência parcial"
        else:
            base = "Confiança alta — evidência robusta"

        if reasons:
            return f"{base}. Fatores: {', '.join(reasons)}"
        return base

    def _record_observation(self, features: Dict, raw: float, calibrated: float):
        self.history.append({
            'features': features,
            'raw_score': raw,
            'calibrated': calibrated,
            'timestamp': time.time()
        })
        if len(self.history) > 10000:
            self.history = self.history[-5000:]

    def compute_metrics(self, ground_truth: List[Tuple[bool, float]]) -> CalibrationMetrics:
        if not ground_truth:
            return CalibrationMetrics(0.0, 0.0, 0.0, 0.0, 0)

        n_bins = 10
        bin_boundaries = np.linspace(0, 1, n_bins + 1)
        ece = 0.0
        mce = 0.0
        total = len(ground_truth)

        for i in range(n_bins):
            in_bin = [(correct, conf) for correct, conf in ground_truth
                     if bin_boundaries[i] <= conf < bin_boundaries[i+1]]
            if not in_bin:
                continue
            bin_acc = float(np.mean([c for c, _ in in_bin]))
            bin_conf = float(np.mean([conf for _, conf in in_bin]))
            bin_weight = len(in_bin) / total
            ece += bin_weight * abs(bin_acc - bin_conf)
            mce = max(mce, abs(bin_acc - bin_conf))

        accuracy = float(np.mean([c for c, _ in ground_truth]))
        avg_conf = float(np.mean([conf for _, conf in ground_truth]))

        return CalibrationMetrics(
            ece=ece,
            mce=mce,
            accuracy=accuracy,
            avg_confidence=avg_conf,
            n_samples=total
        )

    def train_on_mit_dataset(self, dataset_path: str):
        """
        Treina a função de calibração utilizando um dataset de calibração no estilo MIT RLCR.
        Espera um JSON com uma lista de instâncias contendo 'raw_score', 'features' e 'correct'.
        """
        try:
            from sklearn.isotonic import IsotonicRegression
            with open(dataset_path, 'r') as f:
                dataset = json.load(f)

            raw_scores = []
            labels = []

            for item in dataset:
                raw_scores.append(item.get("raw_score", 0.5))
                # Label is 1 se a predição foi correta, 0 se incorreta
                labels.append(1 if item.get("correct") else 0)

            if raw_scores and labels:
                iso_reg = IsotonicRegression(out_of_bounds='clip')
                iso_reg.fit(raw_scores, labels)

                class IsotonicWrapper:
                    def __init__(self, model):
                        self.model = model

                    def predict(self, features: Dict) -> float:
                        raw = features.get('raw_score', 0.5)
                        # IsotonicRegression.predict returns an array
                        calibrated = float(self.model.predict([raw])[0])
                        return calibrated

                self.calibration_function = IsotonicWrapper(iso_reg)
                print(f"Treinamento no MIT dataset concluído com sucesso. {len(raw_scores)} instâncias processadas.")
        except Exception as e:
            print(f"Erro ao treinar no dataset MIT: {e}")

    def _load_calibration_function(self, model_path: Optional[str]):
        class SimpleTemperature:
            def __init__(self, T: float = 1.5):
                self.T = T
            def predict(self, features: Dict) -> float:
                raw = features['raw_score']
                calibrated = 1 / (1 + np.exp(-(2 * raw - 1) / self.T))
                return calibrated
        return SimpleTemperature()
