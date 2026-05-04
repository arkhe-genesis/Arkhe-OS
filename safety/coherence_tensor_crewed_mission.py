import numpy as np
from dataclasses import dataclass
from typing import Dict, Tuple

@dataclass
class CrewedMissionCoherenceTensor4D:
    """Tensor de coerência 4D adaptado para missões tripuladas de longa duração."""

    # Dimensões críticas para missões tripuladas
    crew_health_margin: float  # ε_H: margem de saúde da tripulação = (H_max - H_current)/H_max
    system_reliability: float  # ε_R: confiabilidade de sistemas críticos [0,1]
    communication_latency_min: float  # ε_τ: latência mínima Terra-destino [min] (física da luz)
    radiation_dose_mSv_year: float  # ε_D: dose de radiação acumulada [mSv/ano]

    # Alvos e limites hard para missões tripuladas
    @staticmethod
    def targets() -> 'CrewedMissionCoherenceTensor4D':
        return CrewedMissionCoherenceTensor4D(
            crew_health_margin=0.95,      # 95% da margem de saúde ideal
            system_reliability=0.999,     # 99.9% confiabilidade de sistemas críticos
            communication_latency_min=43, # min (média Terra-Júpiter)
            radiation_dose_mSv_year=50    # mSv/ano (NASA standard para missões de longa duração)
        )

    @staticmethod
    def hard_limits() -> Dict[str, Tuple[float, float]]:
        return {
            'crew_health_margin': (0.90, 1.00),  # Margem de saúde mínima 90%
            'system_reliability': (0.995, 1.00), # Confiabilidade mínima 99.5%
            'communication_latency_min': (3, 53), # Física da luz: Terra-Marte (3 min) a Terra-Júpiter (53 min)
            'radiation_dose_mSv_year': (0, 100)  # Dose máxima anual 100 mSv (limite absoluto)
        }

    def is_within_limits(self) -> bool:
        """Verifica se todas as dimensões estão dentro de limites hard para segurança da tripulação."""
        limits = self.hard_limits()
        return all(
            limits[dim][0] <= getattr(self, dim) <= limits[dim][1]
            for dim in ['crew_health_margin', 'system_reliability', 'communication_latency_min', 'radiation_dose_mSv_year']
        )

    def compute_coherence_score(self) -> float:
        """Calcula score de coerência harmônico para missões tripuladas (penaliza fortemente riscos à tripulação)."""
        targets = self.targets()
        limits = self.hard_limits()

        scores = []
        for dim in ['crew_health_margin', 'system_reliability', 'communication_latency_min', 'radiation_dose_mSv_year']:
            value = getattr(self, dim)
            target = getattr(targets, dim)
            low, high = limits[dim]

            # Score específico por dimensão com pesos de segurança
            if dim == 'crew_health_margin':
                # Saúde da tripulação: peso máximo, unilateral (maior é melhor)
                weight = 4.0
                score = 1.0 if value >= target else value / target
            elif dim == 'system_reliability':
                # Confiabilidade de sistemas: peso alto, unilateral
                weight = 3.0
                score = 1.0 if value >= target else value / target
            elif dim == 'communication_latency_min':
                # Latência: valor fixo pela física; score = 1.0 se dentro de limites
                weight = 1.0
                score = 1.0 if low <= value <= high else 0.0
            elif dim == 'radiation_dose_mSv_year':
                # Dose de radiação: menor é melhor (inverso)
                weight = 3.0
                score = 1.0 if value <= target else target / max(value, 1e-6)
            else:
                # Fallback genérico
                weight = 1.0
                std = (high - low) / 6
                score = np.exp(-(value - target)**2 / (2 * std**2))

            # Aplicar peso e garantir bounds
            weighted_score = min(1.0, score ** (1.0/weight))
            scores.append(max(0.0, weighted_score))

        # Média harmônica ponderada: penaliza fortemente qualquer dimensão crítica fraca
        weights = [4.0, 3.0, 1.0, 3.0]
        weighted_harmonic = sum(weights) / sum(w/max(s, 1e-6) for w, s in zip(weights, scores))
        return weighted_harmonic
