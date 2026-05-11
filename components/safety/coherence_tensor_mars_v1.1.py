from dataclasses import dataclass
from typing import Dict, Tuple
import numpy as np

@dataclass
class MarsCoherenceTensor4D:
    """Tensor de coerência 4D revisado para operações marcianas."""

    # Dimensões físicas validadas
    phase_sync: float          # ε_φ: sincronismo de disparo de bobinas [rad]
    command_latency_us: float  # ε_τ: latência comando→atuação [µs]
    power_peak_mw: float       # ε_ρ: consumo de potência de pico [MW]
    thermal_margin: float      # ε_T: margem térmica = (T_max - T_op)/T_max [unitless]

    # Alvos e limites hard para Marte
    @staticmethod
    def targets() -> 'MarsCoherenceTensor4D':
        return MarsCoherenceTensor4D(
            phase_sync=0.07,        # rad
            command_latency_us=500, # µs
            power_peak_mw=1750,     # MW (corrigido)
            thermal_margin=0.95     # 95% da margem térmica disponível
        )

    @staticmethod
    def hard_limits() -> Dict[str, Tuple[float, float]]:
        return {
            'phase_sync': (0.04, 0.10),
            'command_latency_us': (400, 600),
            'power_peak_mw': (1500, 2000),  # Corrigido para 1.75 GW pico
            'thermal_margin': (0.90, 1.00)   # Margem térmica mínima 90%
        }

    def is_within_limits(self) -> bool:
        """Verifica se todas as dimensões estão dentro de limites hard."""
        limits = self.hard_limits()
        return all(
            limits[dim][0] <= getattr(self, dim) <= limits[dim][1]
            for dim in ['phase_sync', 'command_latency_us', 'power_peak_mw', 'thermal_margin']
        )

    def compute_coherence_score(self) -> float:
        """Calcula score de coerência harmônico (penaliza dimensões fracas)."""
        targets = self.targets()
        limits = self.hard_limits()

        scores = []
        for dim in ['phase_sync', 'command_latency_us', 'power_peak_mw', 'thermal_margin']:
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