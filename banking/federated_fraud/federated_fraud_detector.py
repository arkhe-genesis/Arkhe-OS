#!/usr/bin/env python3
"""
Substrato 200.1: Federated Fraud Detector
Detecção de fraudes entre instituições financeiras sem compartilhar
dados sensíveis. Utiliza Federated Learning com Differential Privacy.
"""

import asyncio
import hashlib
import json
import time
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class FraudIndicatorReport:
    """Relatório de indicadores de fraude (sem dados brutos)."""
    institution_id: str
    timestamp: float
    total_transactions: int
    flagged_transactions: int
    fraud_patterns: Dict[str, int]  # pattern_type → count
    feature_distributions: Dict[str, Dict[str, float]]  # feature → {mean, std, min, max}
    dp_noise_epsilon: float = 2.0
    model_weights_hash: Optional[str] = None

@dataclass
class FederatedFraudAlert:
    """Alerta de fraude cross‑org gerado pelo modelo federado."""
    alert_id: str
    pattern_type: str
    institutions_affected: List[str]
    confidence_score: float
    recommended_actions: List[str]
    temporal_seal: Optional[str] = None
    created_at: float = field(default_factory=time.time)

class FederatedFraudDetector:
    """
    Detector de fraudes federado entre instituições financeiras.

    Princípios:
    • Cada banco treina seu modelo local (dados NUNCA saem)
    • Compartilham-se apenas gradientes/indicadores com ruído DP
    • Agregação federada (FedAvg) para modelo global
    • Alertas cross‑org quando padrões de fraude similares detectados
    • Privacidade diferencial (ε=2.0) em todos os compartilhamentos
    """

    # Padrões de fraude conhecidos
    FRAUD_PATTERNS = [
        "layering",
        "structuring",
        "rapid_movement",
        "unusual_beneficiary",
        "geographic_anomaly",
        "time_pattern_anomaly",
        "amount_anomaly",
        "velocity_spike"
    ]

    def __init__(
        self,
        institution_id: str,
        phi_bus=None,
        temporal_chain=None,
        privacy_epsilon: float = 2.0,
        federation_round_interval_hours: int = 4
    ):
        self.institution_id = institution_id
        self.phi_bus = phi_bus
        self.temporal = temporal_chain
        self.epsilon = privacy_epsilon
        self.round_interval = federation_round_interval_hours

        self._local_model_weights: Optional[np.ndarray] = None
        self._global_model_weights: Optional[np.ndarray] = None
        self._partner_reports: Dict[str, List[FraudIndicatorReport]] = defaultdict(list)
        self._cross_org_alerts: List[FederatedFraudAlert] = []
        self._federation_round = 0

    async def train_local_model(self, local_transactions: List[Dict]) -> np.ndarray:
        """
        Treina modelo local de detecção de fraude.

        Dados NUNCA saem da instituição.
        Apenas os gradientes (com ruído DP) são compartilhados.
        """
        # Extrair features das transações locais
        features = self._extract_features(local_transactions)

        # Treinar Isolation Forest local (mock)
        n_features = len(self.FRAUD_PATTERNS) + 3  # patterns + amount + time + velocity
        self._local_model_weights = np.random.randn(n_features) * 0.1

        logger.info(f"🧠 Modelo local treinado: {len(local_transactions)} transações")
        return self._local_model_weights

    def _extract_features(self, transactions: List[Dict]) -> np.ndarray:
        """Extrai features para treinamento (mock)."""
        n = len(transactions)
        n_features = len(self.FRAUD_PATTERNS) + 3
        return np.random.randn(n, n_features)

    async def generate_fraud_report(self) -> FraudIndicatorReport:
        """
        Gera relatório de indicadores de fraude com privacidade diferencial.

        Este relatório é compartilhado com outras instituições
        sem revelar dados brutos de transações.
        """
        # Coletar estatísticas locais
        pattern_counts = {
            pattern: np.random.randint(0, 10)
            for pattern in self.FRAUD_PATTERNS
        }

        # Aplicar ruído Laplace para privacidade diferencial
        noisy_patterns = {}
        for pattern, count in pattern_counts.items():
            noise = int(np.random.laplace(0, 1.0 / self.epsilon))
            noisy_patterns[pattern] = max(0, count + noise)

        # Gerar distribuições de features (com ruído DP)
        feature_distributions = {}
        for i, pattern in enumerate(self.FRAUD_PATTERNS):
            mean_val = np.random.uniform(0.1, 0.5)
            feature_distributions[pattern] = {
                "mean": round(mean_val + np.random.laplace(0, 0.1 / self.epsilon), 3),
                "std": round(0.1 + np.random.laplace(0, 0.05 / self.epsilon), 3),
                "min": 0.0,
                "max": 1.0
            }

        report = FraudIndicatorReport(
            institution_id=self.institution_id,
            timestamp=time.time(),
            total_transactions=np.random.randint(10000, 100000),
            flagged_transactions=sum(noisy_patterns.values()),
            fraud_patterns=noisy_patterns,
            feature_distributions=feature_distributions,
            dp_noise_epsilon=self.epsilon,
            model_weights_hash=hashlib.sha3_256(
                self._local_model_weights.tobytes() if self._local_model_weights is not None else b""
            ).hexdigest()[:16] if self._local_model_weights is not None else None
        )

        return report

    async def submit_report_to_federation(self, report: FraudIndicatorReport) -> Dict:
        """
        Submete relatório de fraude à federação.

        O relatório é publicado no Phi‑Bus para que outras instituições
        possam correlacionar padrões de fraude.
        """
        # Validar privacidade
        if report.dp_noise_epsilon < self.epsilon:
            return {"status": "rejected", "reason": "insufficient_privacy"}

        # Armazenar localmente
        self._partner_reports[report.institution_id].append(report)

        # Publicar no Phi‑Bus para outras instituições
        if self.phi_bus:
            await self.phi_bus.publish_metric("federated_fraud_report", {
                "institution_id": report.institution_id,
                "flagged_transactions": report.flagged_transactions,
                "top_patterns": sorted(
                    report.fraud_patterns.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:3],
                "timestamp": report.timestamp
            })

        # Verificar correlação cross‑org
        alert = await self._check_cross_org_patterns(report)
        if alert:
            await self._trigger_federated_alert(alert)

        return {"status": "accepted", "cross_org_alert": alert is not None}

    async def _check_cross_org_patterns(self, new_report: FraudIndicatorReport) -> Optional[FederatedFraudAlert]:
        """
        Verifica se padrões de fraude similares apareceram em outras instituições.

        Critérios para alerta cross‑org:
        • 3+ instituições reportam o mesmo padrão de fraude
        • Janela temporal de 6 horas
        • Padrão com contagem significativa (>5 ocorrências)
        """
        window = 6 * 3600  # 6 horas
        threshold_insts = 3
        threshold_count = 5

        for pattern, count in new_report.fraud_patterns.items():
            if count < threshold_count:
                continue

            # Verificar outras instituições com o mesmo padrão
            affected_insts = {new_report.institution_id}
            for inst_id, reports in self._partner_reports.items():
                recent = [r for r in reports if abs(r.timestamp - new_report.timestamp) < window]
                if recent and recent[-1].fraud_patterns.get(pattern, 0) >= threshold_count:
                    affected_insts.add(inst_id)

            if len(affected_insts) >= threshold_insts:
                return FederatedFraudAlert(
                    alert_id=hashlib.sha3_256(
                        f"{pattern}:{list(affected_insts)}:{time.time()}".encode()
                    ).hexdigest()[:12],
                    pattern_type=pattern,
                    institutions_affected=list(affected_insts),
                    confidence_score=min(1.0, len(affected_insts) / 5),
                    recommended_actions=self._get_fraud_actions(pattern)
                )

        return None

    def _get_fraud_actions(self, pattern_type: str) -> List[str]:
        """Retorna ações recomendadas por tipo de fraude."""
        actions = {
            "layering": ["🔍 Investigar múltiplas camadas de transações", "📋 Revisar KYC do cliente"],
            "structuring": ["🚨 Reportar ao COAF", "🔒 Bloquear conta temporariamente"],
            "rapid_movement": ["⚡ Ativar verificação adicional para transferências", "📞 Contatar cliente"],
            "unusual_beneficiary": ["🔐 Exigir autenticação multifator", "📋 Atualizar lista de beneficiários"],
            "geographic_anomaly": ["🌍 Verificar geolocalização do dispositivo", "🔒 Bloquear transações internacionais"],
        }
        return actions.get(pattern_type, ["📊 Monitorar padrão por 24h", "📋 Registrar para auditoria"])

    async def _trigger_federated_alert(self, alert: FederatedFraudAlert):
        """Dispara alerta federado e ancora na TemporalChain."""
        # Ancorar na TemporalChain
        if self.temporal:
            alert.temporal_seal = await self.temporal.anchor_event(
                "federated_fraud_alert",
                {
                    "alert_id": alert.alert_id,
                    "pattern_type": alert.pattern_type,
                    "institutions_affected": alert.institutions_affected,
                    "confidence_score": alert.confidence_score,
                    "timestamp": alert.created_at
                }
            )

        self._cross_org_alerts.append(alert)

        logger.warning(
            f"🚨 ALERTA DE FRAUDE FEDERADO: {alert.alert_id} | "
            f"Padrão: {alert.pattern_type} | "
            f"Instituições: {len(alert.institutions_affected)} | "
            f"Confiança: {alert.confidence_score:.2f}"
        )

        # Publicar no Phi‑Bus
        if self.phi_bus:
            await self.phi_bus.publish_metric("federated_fraud_alert", {
                "alert_id": alert.alert_id,
                "pattern_type": alert.pattern_type,
                "institutions_count": len(alert.institutions_affected)
            })

    def get_federation_statistics(self) -> Dict:
        """Retorna estatísticas da federação de detecção de fraudes."""
        return {
            "federation_round": self._federation_round,
            "partner_institutions": len(self._partner_reports),
            "total_cross_org_alerts": len(self._cross_org_alerts),
            "alert_by_pattern": self._count_alerts_by_pattern(),
            "avg_confidence": np.mean([a.confidence_score for a in self._cross_org_alerts]) if self._cross_org_alerts else 0,
            "privacy_epsilon": self.epsilon
        }

    def _count_alerts_by_pattern(self) -> Dict[str, int]:
        """Conta alertas por padrão de fraude."""
        from collections import Counter
        counter = Counter(a.pattern_type for a in self._cross_org_alerts)
        return dict(counter.most_common())
