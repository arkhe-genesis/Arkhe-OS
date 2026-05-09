#!/usr/bin/env python3
"""
social_phi_rep_integration.py — Integração do Oracle Φ-REP com métricas sociais.
"""
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
import time

@dataclass
class SocialContribution:
    """Contribuição social para cálculo de reputação."""
    contribution_id: str
    contributor_seal: str
    contribution_type: str  # "post", "comment", "curation", "verification", "governance"
    coherence_score: float  # Φ_C da contribuição
    impact_score: float     # Alcance/engajamento ponderado por coerência
    timestamp: float
    verified: bool = True   # Se foi verificada por pares

class SocialPhiRepOracle:
    """
    Oracle de reputação social baseado em Φ-REP.

    Fórmula:
    Φ_REP(user) = α·base_reputation + β·social_contributions + γ·peer_validation + δ·longevity
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or {
            "base_kym": 0.25,           # Reputação inicial do KYM
            "content_quality": 0.35,     # Coerência média das contribuições
            "peer_validation": 0.25,     # Validação por outros usuários
            "longevity_factor": 0.15     # Bónus por tempo na rede
        }
        self.contributions: Dict[str, List[SocialContribution]] = {}

    def record_contribution(self, contribution: SocialContribution):
        """Registra nova contribuição social."""
        if contribution.contributor_seal not in self.contributions:
            self.contributions[contribution.contributor_seal] = []
        self.contributions[contribution.contributor_seal].append(contribution)

    def calculate_reputation(self,
                            seal: str,
                            current_time: Optional[float] = None) -> float:
        """Calcula reputação Φ-REP social para um usuário."""
        if current_time is None:
            current_time = time.time()

        contributions = self.contributions.get(seal, [])
        if not contributions:
            return 0.5  # Reputação neutra inicial

        # 1. Fator base do KYM (placeholder: 0.7 para usuários verificados)
        base_kym = 0.7

        # 2. Qualidade de conteúdo: média ponderada de coerência
        if contributions:
            total_impact = sum(c.impact_score for c in contributions)
            if total_impact > 0:
                content_quality = sum(
                    c.coherence_score * c.impact_score for c in contributions
                ) / total_impact
            else:
                content_quality = np.mean([c.coherence_score for c in contributions])
        else:
            content_quality = 0.5

        # 3. Validação por pares: fração de contribuições verificadas
        verified_ratio = sum(1 for c in contributions if c.verified) / len(contributions)
        peer_validation = verified_ratio

        # 4. Fator de longevidade: bónus por tempo na rede
        oldest = min(c.timestamp for c in contributions)
        days_active = (current_time - oldest) / 86400
        longevity_factor = min(1.0, days_active / 365)  # Saturação em 1 ano

        # Combinação ponderada
        phi_rep = (
            self.weights["base_kym"] * base_kym +
            self.weights["content_quality"] * float(content_quality) +
            self.weights["peer_validation"] * peer_validation +
            self.weights["longevity_factor"] * longevity_factor
        )

        return float(min(1.0, max(0.0, phi_rep)))

    def get_top_contributors(self,
                            limit: int = 10,
                            time_window_days: Optional[int] = None) -> List[Dict]:
        """Retorna top contribuidores por reputação."""
        current_time = time.time()
        cutoff = current_time - (time_window_days * 86400) if time_window_days else 0

        ranked = []
        for seal, contributions in self.contributions.items():
            # Filtrar por janela temporal se especificado
            if time_window_days:
                contributions = [c for c in contributions if c.timestamp >= cutoff]
            if not contributions:
                continue

            phi_rep = self.calculate_reputation(seal, current_time)
            total_impact = sum(c.impact_score for c in contributions)

            ranked.append({
                "seal": seal,
                "phi_rep": round(phi_rep, 3),
                "contribution_count": len(contributions),
                "total_impact": round(total_impact, 2),
                "avg_coherence": round(float(np.mean([c.coherence_score for c in contributions])), 3)
            })

        # Ordenar por Φ-REP descendente
        ranked.sort(key=lambda x: x["phi_rep"], reverse=True)
        return ranked[:limit]
