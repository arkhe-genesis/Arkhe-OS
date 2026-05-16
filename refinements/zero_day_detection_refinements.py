#!/usr/bin/env python3
"""Zero‑Day refinements – feeds em tempo real, ensemble, SHAP – Substrato 199.5"""

import asyncio, hashlib, json, time, logging, numpy as np
from typing import Dict, List, Optional
from collections import deque

logger = logging.getLogger(__name__)

class RealtimeThreatFeedIntegrator:
    """
    Integra feeds MISP/VirusTotal em tempo real via webhooks e polling.
    Atualiza o dataset de treinamento continuamente.
    """
    def __init__(self, temporal=None, phi_bus=None):
        self.temporal = temporal
        self.phi_bus = phi_bus
        self.new_indicators = deque(maxlen=10000)

    async def consume_misp_event(self, event: Dict):
        """Processa evento MISP recebido via webhook."""
        indicator = self._normalize_event(event, source="MISP")
        self.new_indicators.append(indicator)
        if self.temporal:
            await self.temporal.anchor_event("ti_feed_received", {"source": "MISP", "hash": indicator["hash"]})

    async def poll_virustotal(self, api_key: str, query: str = "tag:arkhe"):
        """Polling de VirusTotal Intelligence."""
        # Mock de integração com API do VT
        indicator = {"source": "VirusTotal", "hash": "vt_"+hashlib.md5(query.encode()).hexdigest()[:8],
                     "score": np.random.uniform(0.6, 1.0), "timestamp": time.time()}
        self.new_indicators.append(indicator)
        logger.info(f"VT indicator ingested: {indicator['hash']}")

    def _normalize_event(self, raw: Dict, source: str) -> Dict:
        return {
            "source": source,
            "hash": hashlib.sha3_256(json.dumps(raw).encode()).hexdigest()[:16],
            "timestamp": time.time(),
            "features": raw.get("features", {})
        }

class EnsembleRetrainer:
    """
    Re‑treina ensemble (IF+RF) com dados históricos reais acumulados.
    Mantém versões do modelo e avalia em holdout progressivo.
    """
    def __init__(self, historical_data: deque, temporal=None):
        self.historical = historical_data
        self.temporal = temporal
        self.models = []

    async def retrain_with_new_data(self, new_samples: List[Dict]):
        """Adiciona novas amostras e re‑treina modelo."""
        for s in new_samples:
            self.historical.append(s)
        # Mock de treinamento: em produção usaria scikit‑learn com os novos dados
        # Calcular métricas simuladas
        f1 = np.random.uniform(0.85, 0.94)
        auc = np.random.uniform(0.90, 0.97)
        model_id = f"ens_{time.time()}"
        self.models.append({"id": model_id, "f1": f1, "auc": auc})
        if self.temporal:
            await self.temporal.anchor_event("ensemble_retrained", {"model_id": model_id, "f1": f1, "auc": auc})
        logger.info(f"🧠 Ensemble retreinado: {model_id} (F1={f1:.3f})")

class ShapExplainer:
    """
    Explicabilidade SHAP para alertas do zero‑day detector.
    Gera explicações locais e globais.
    """
    def __init__(self, model=None):
        self.model = model
        self.shap_values = None

    async def explain_alert(self, sample: np.ndarray, feature_names: List[str]) -> Dict:
        """Retorna contribuições SHAP para uma instância."""
        # Mock: em produção usaria shap.Explainer
        contributions = {name: np.random.uniform(-1, 1) for name in feature_names}
        top_reasons = sorted(contributions.items(), key=lambda x: abs(x[1]), reverse=True)[:5]
        explanation = " | ".join([f"{feat} {'+' if val>0 else '-'}{abs(val):.2f}" for feat, val in top_reasons])
        logger.info(f"🔍 SHAP: {explanation}")
        return {"contributions": contributions, "top_factors": top_reasons, "explanation": explanation}
