import numpy as np
from scipy import stats
from typing import Literal, Union
from ..harness import CoherenceCalculator

class AdvancedCoherenceCalculator(CoherenceCalculator):
    """Calculadora de coerência com suporte a distribuições não-gaussianas."""

    def compute_robust(
# arkhe_os/validation/experimental_harness/coherence/calculator.py
"""Cálculo de coerência entre valor observado e predição Ψ_ToE."""
import numpy as np

class CoherenceCalculator:
    def __init__(self, mercy_gap: tuple = (0.04, 0.10)):
        self.mercy_gap = mercy_gap

    def compute(
        self,
        observed: float,
        observed_err: float,
        predicted: float,
        predicted_err: float,
        distribution: Literal['gaussian', 'student-t', 'laplace'] = 'gaussian',
        dof: float = 4.0  # graus de liberdade para Student-t
    ) -> tuple[float, bool]:
        """
        Calcula Φ_C usando diferentes modelos de incerteza.

        Args:
            distribution: modelo estatístico para as incertezas
            dof: graus de liberdade (apenas para Student-t)
        predicted_err: float
    ) -> tuple[float, bool]:
        """
        Calcula Φ_C como decaimento gaussiano da diferença normalizada.
        Retorna (coherence, mercy_gap_valid).
        """
        if np.isnan(observed) or predicted == 0:
            return 0.0, False

        delta = abs(observed - predicted)

        if distribution == 'gaussian':
            sigma = np.sqrt(observed_err**2 + predicted_err**2 + 1e-10)
            normalized_delta = delta / sigma
            coherence = np.exp(-0.5 * normalized_delta**2)

        elif distribution == 'student-t':
            # Mais robusto a outliers; caudas mais pesadas
            sigma = np.sqrt(observed_err**2 + predicted_err**2 + 1e-10)
            t_stat = delta / sigma
            # Coerência como probabilidade acumulada da cauda
            coherence = 1 - stats.t.cdf(abs(t_stat), df=dof)
            coherence = max(0.0, min(1.0, coherence * 2))  # Normalizar para [0,1]

        elif distribution == 'laplace':
            # Distribuição de Laplace (exponencial dupla)
            b = np.sqrt(observed_err**2 + predicted_err**2 + 1e-10) / np.sqrt(2)
            coherence = np.exp(-abs(delta) / b)

        else:
            raise ValueError(f"Distribuição não suportada: {distribution}")

        # Mercy gap validation (invariante ao modelo)
        relative_delta = delta / abs(predicted) if predicted != 0 else 0.0
        mercy_valid = self.mercy_gap[0] <= relative_delta <= self.mercy_gap[1]

        return float(coherence), mercy_valid
        # Diferença normalizada pela incerteza combinada
        delta = abs(observed - predicted)
        sigma = np.sqrt(observed_err**2 + predicted_err**2 + 1e-10)

        # Coerência: Φ_C = exp(-(delta/sigma)^2 / 2)
        normalized_delta = delta / sigma
        coherence = np.exp(-0.5 * normalized_delta**2)

        # Mercy gap: a diferença relativa deve estar entre 0.04 e 0.10
        relative_delta = delta / abs(predicted) if predicted != 0 else 0.0
        mercy_valid = (self.mercy_gap[0] <= relative_delta <= self.mercy_gap[1])

        return float(coherence), mercy_valid
