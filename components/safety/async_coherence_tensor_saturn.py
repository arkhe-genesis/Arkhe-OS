import numpy as np
from dataclasses import dataclass
from typing import Dict, Tuple

@dataclass
class SaturnAsyncCoherenceTensor:
    """Tensor de coerência para operações assíncronas no sistema de Saturno."""

    # Dimensões assíncronas validadas
    crdt_convergence_hours: float  # ε_κ: tempo para convergência de CRDTs [horas]
    merkle_sync_success_rate: float  # ε_μ: taxa de sucesso de sincronização semanal [0,1]
    local_decision_latency_s: float  # ε_δ: latência para decisões locais [segundos]
    ethical_compliance_zk_verified: float  # ε_ζ: fração de decisões com ZK-proof ético [0,1]

    # Alvos e limites para operações assíncronas em Saturno
    @staticmethod
    def targets() -> 'SaturnAsyncCoherenceTensor':
        return SaturnAsyncCoherenceTensor(
            crdt_convergence_hours=24.0,    # Convergência em ≤24 horas
            merkle_sync_success_rate=0.95,  # 95% de sucesso em sync semanal
            local_decision_latency_s=10.0,  # Decisões locais em ≤10 segundos
            ethical_compliance_zk_verified=1.0  # 100% das decisões críticas com ZK-proof
        )

    @staticmethod
    def hard_limits() -> Dict[str, Tuple[float, float]]:
        return {
            'crdt_convergence_hours': (12.0, 48.0),  # Convergência entre 12-48 horas
            'merkle_sync_success_rate': (0.85, 1.0),  # Sucesso mínimo 85%
            'local_decision_latency_s': (1.0, 30.0),  # Decisões locais entre 1-30 segundos
            'ethical_compliance_zk_verified': (0.99, 1.0)  # Mínimo 99% de decisões com ZK-proof
        }

    def is_async_operational(self) -> bool:
        """Verifica se o nó está operacional dentro de limites assíncronos."""
        limits = self.hard_limits()
        return all(
            limits[dim][0] <= getattr(self, dim) <= limits[dim][1]
            for dim in ['crdt_convergence_hours', 'merkle_sync_success_rate',
                       'local_decision_latency_s', 'ethical_compliance_zk_verified']
        )

    def compute_async_coherence_score(self) -> float:
        """Calcula score de coerência assíncrona com pesos para autonomia ética."""
        targets = self.targets()
        limits = self.hard_limits()

        scores = []
        weights = [1.0, 2.0, 1.0, 3.0]  # Peso maior para conformidade ética

        for dim, weight in zip(['crdt_convergence_hours', 'merkle_sync_success_rate',
                               'local_decision_latency_s', 'ethical_compliance_zk_verified'], weights):
            value = getattr(self, dim)
            target = getattr(targets, dim)
            low, high = limits[dim]

            if dim == 'crdt_convergence_hours':
                # Menor tempo de convergência é melhor (inverso)
                score = 1.0 if value <= target else target / value
            elif dim == 'merkle_sync_success_rate':
                # Maior taxa de sucesso é melhor (unilateral)
                score = 1.0 if value >= target else value / target
            elif dim == 'local_decision_latency_s':
                # Menor latência é melhor (inverso)
                score = 1.0 if value <= target else target / value
            elif dim == 'ethical_compliance_zk_verified':
                # Conformidade ética: crítico, peso alto
                score = 1.0 if value >= target else value / target
            else:
                # Fallback genérico
                std = (high - low) / 6
                score = np.exp(-(value - target)**2 / (2 * std**2))

            # Aplicar peso e garantir bounds
            weighted_score = min(1.0, score ** (1.0/weight))
            scores.append(max(0.0, weighted_score))

        # Média harmônica ponderada: penaliza fortemente conformidade ética baixa
        weighted_harmonic = sum(weights) / sum(w/s for w, s in zip(weights, scores))
        return weighted_harmonic
