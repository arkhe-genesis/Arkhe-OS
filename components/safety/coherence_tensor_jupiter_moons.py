import numpy as np
from dataclasses import dataclass
from typing import Dict, Tuple

@dataclass
class JupiterMoonsCoherenceTensor4D:
    """Tensor de coerência 4D adaptado para exploração em luas de Júpiter."""

    # Dimensões físicas validadas para ambiente de radiação extrema
    phase_sync: float          # ε_φ: sincronismo de sistemas científicos [rad]
    command_latency_min: float # ε_τ: latência mínima Terra-Júpiter [min] (física da luz)
    power_w: float             # ε_ρ: consumo de potência de sistemas científicos [W]
    radiation_margin: float    # ε_R: margem de blindagem = (D_max - D_op)/D_max [unitless]

    # Alvos e limites hard para luas de Júpiter
    @staticmethod
    def targets() -> 'JupiterMoonsCoherenceTensor4D':
        return JupiterMoonsCoherenceTensor4D(
            phase_sync=0.07,        # rad
            command_latency_min=43, # min (média Terra-Júpiter)
            power_w=700,            # W (consumo médio de sistemas científicos)
            radiation_margin=0.95   # 95% da margem de blindagem disponível
        )

    @staticmethod
    def hard_limits() -> Dict[str, Tuple[float, float]]:
        return {
            'phase_sync': (0.04, 0.10),
            'command_latency_min': (33, 53),  # Física da luz: não negociável
            'power_w': (650, 750),
            'radiation_margin': (0.90, 1.00)  # Margem de blindagem mínima 90%
        }

    def is_within_limits(self) -> bool:
        """Verifica se todas as dimensões estão dentro de limites hard."""
        limits = self.hard_limits()
        return all(
            limits[dim][0] <= getattr(self, dim) <= limits[dim][1]
            for dim in ['phase_sync', 'command_latency_min', 'power_w', 'radiation_margin']
        )

    def compute_coherence_score(self) -> float:
        """Calcula score de coerência harmônico para operações em Júpiter."""
        targets = self.targets()
        limits = self.hard_limits()

        scores = []
        for dim in ['phase_sync', 'command_latency_min', 'power_w', 'radiation_margin']:
            value = getattr(self, dim)
            target = getattr(targets, dim)
            low, high = limits[dim]

            # Score gaussiano centrado no alvo
            if dim == 'radiation_margin':
                # Margem de radiação: maior é melhor (unilateral)
                score = 1.0 if value >= target else value / target
            elif dim == 'command_latency_min':
                # Latência: valor fixo pela física; score = 1.0 se dentro de limites
                score = 1.0 if low <= value <= high else 0.0
            else:
                # Outras dimensões: bilateral
                std = (high - low) / 6  # Assumir 3σ cobrem o intervalo
                score = np.exp(-(value - target)**2 / (2 * std**2))

            scores.append(max(0.0, min(1.0, score)))

        # Média harmônica: penaliza fortemente qualquer dimensão fraca
        harmonic = len(scores) / sum(1.0 / max(s, 1e-6) for s in scores)
        return harmonic
