import numpy as np

class AdaptiveBaselineEstimator:
    """Mantém baseline dinâmica por destino usando média móvel exponencial."""

    def __init__(self, alpha: float = 0.1, r_max: float = 1000.0):
        self.alpha = alpha  # Fator de suavização
        self.r_max = r_max
        self.baselines: dict[str, float] = {}

    def update_baseline(self, target: str, rtt: float) -> float:
        """Atualiza baseline EMA e retorna valor atual."""
        if target not in self.baselines:
            self.baselines[target] = rtt  # Inicializa com primeira medição
        else:
            self.baselines[target] = (
                self.alpha * rtt + (1 - self.alpha) * self.baselines[target]
            )
        return self.baselines[target]

    def compute_coherence(self, target: str, rtt_avg: float, loss: float, jitter: float) -> float:
        r_base = self.baselines.get(target, rtt_avg)
        # Avoid negative values inside the exponential / factors
        latency_factor = max(0.0, 1 - (rtt_avg - r_base) / (self.r_max - r_base + 1e-6))
        reliability_factor = 1 - loss
        jitter_factor = np.exp(-0.1 * jitter)
        return max(0.0, min(1.0, latency_factor * reliability_factor * jitter_factor))
