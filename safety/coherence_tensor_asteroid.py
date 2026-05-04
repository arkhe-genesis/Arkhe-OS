import numpy as np
from dataclasses import dataclass
from typing import Dict, Tuple

@dataclass
class AsteroidCoherenceTensor4D:
    """Tensor de coerência 4D adaptado para operações no cinturão de asteroides."""

    # Dimensões físicas validadas para ambiente de microgravidade
    phase_sync: float          # ε_φ: sincronismo de bobinas/sistemas [rad]
    command_latency_ms: float  # ε_τ: latência comando→atuação [ms] (maior que Terra)
    power_kw: float            # ε_ρ: consumo de potência de processamento [kW]
    thermal_margin: float      # ε_T: margem térmica = (T_max - T_op)/T_max [unitless]

    # Alvos e limites hard para cinturão de asteroides
    @staticmethod
    def targets() -> 'AsteroidCoherenceTensor4D':
        return AsteroidCoherenceTensor4D(
            phase_sync=0.07,        # rad
            command_latency_ms=50,  # ms (latência de comunicação + processamento)
            power_kw=750,           # kW (consumo médio de processamento)
            thermal_margin=0.95     # 95% da margem térmica disponível
        )

    @staticmethod
    def hard_limits() -> Dict[str, Tuple[float, float]]:
        return {
            'phase_sync': (0.04, 0.10),
            'command_latency_ms': (40, 60),
            'power_kw': (700, 800),
            'thermal_margin': (0.90, 1.00)
        }

    def is_within_limits(self) -> bool:
        """Verifica se todas as dimensões estão dentro de limites hard."""
        limits = self.hard_limits()
        return all(
            limits[dim][0] <= getattr(self, dim) <= limits[dim][1]
            for dim in ['phase_sync', 'command_latency_ms', 'power_kw', 'thermal_margin']
        )

    def compute_coherence_score(self) -> float:
        """Calcula score de coerência harmônico para operações de asteroides."""
        targets = self.targets()
        limits = self.hard_limits()

        scores = []
        for dim in ['phase_sync', 'command_latency_ms', 'power_kw', 'thermal_margin']:
            value = getattr(self, dim)
            target = getattr(targets, dim)
            low, high = limits[dim]

            # Score gaussiano centrado no alvo
            if dim == 'thermal_margin':
                # Margem térmica: maior é melhor (unilateral)
                score = 1.0 if value >= target else value / target
            else:
                # Outras dimensões: bilateral
                std = (high - low) / 6  # Assumir 3σ cobrem o intervalo
                score = np.exp(-(value - target)**2 / (2 * std**2))

            scores.append(max(0.0, min(1.0, score)))

        # Média harmônica: penaliza fortemente qualquer dimensão fraca
        harmonic = len(scores) / sum(1.0 / max(s, 1e-6) for s in scores)
        return harmonic
