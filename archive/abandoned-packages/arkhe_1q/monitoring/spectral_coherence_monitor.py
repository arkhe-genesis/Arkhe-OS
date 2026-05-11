# arkhe_1q/monitoring/spectral_coherence_monitor.py
import torch
import numpy as np
from collections import deque
from typing import Dict, Tuple

class SpectralCoherenceMonitor:
    """
    Monitor de coerência espectral Φ_C(λ) via estimativa de Lanczos hierárquico.
    """

    def __init__(self, num_scales: int = 8, lanczos_batch_size: int = 64,
                 eigenvalue_range: Tuple[float, float] = (1e-3, 1e2)):
        self.num_scales = num_scales
        self.batch_size = lanczos_batch_size
        self.lambda_min, self.lambda_max = eigenvalue_range

        # Escalas logarítmicas para Φ_C(λ)
        self.scales = torch.logspace(
            torch.log10(torch.tensor(self.lambda_min)),
            torch.log10(torch.tensor(self.lambda_max)),
            num_scales
        )

        # Cache de espectros recentes
        self.spectrum_history: deque = deque(maxlen=100)

        # Thresholds para detecção de pico local
        self.peak_detection_window = 10
        self.peak_threshold_ratio = 1.1

    def compute_spectrum(self, forms: Dict[int, torch.Tensor],
                        num_eigenvalues: int = 32) -> torch.Tensor:
        """
        Computa espectro de coerência Φ_C(λ) para múltiplas escalas.
        """
        # Concatenar formas de diferentes graus para espectro unificado
        # (em produção: tratar cada grau separadamente e combinar)
        combined = torch.cat([forms[k].view(forms[k].shape[0], -1)
                            for k in sorted(forms.keys())], dim=1)

        # Estimar autovalores do Laplaciano de Dirac via Lanczos em batch
        eigenvalues = self._estimate_eigenvalues_lanczos(
            combined, num_eigenvalues=num_eigenvalues
        )

        # Calcular Φ_C(λ) para cada escala
        phi_c_spectrum = torch.zeros(self.num_scales)

        for i, lambda_scale in enumerate(self.scales):
            # Peso de Boltzmann adaptativo por escala
            beta = 1.0 / lambda_scale
            weights = torch.exp(-beta * torch.abs(eigenvalues))
            weights = weights / (weights.sum() + 1e-12)

            # Entropia espectral S_C(λ)
            S_C = -torch.sum(weights * torch.log(weights + 1e-12))

            # Para Φ_C: subtrair entropia de bipartição mínima (simplificação)
            # Em produção: calcular via divisão do manifold
            S_partition_min = S_C * 0.85  # simplificação: 85% da entropia total

            phi_c_spectrum[i] = S_C - S_partition_min

        # Normalizar espectro para [0, 1]
        phi_c_spectrum = (phi_c_spectrum - phi_c_spectrum.min()) / \
                        (phi_c_spectrum.max() - phi_c_spectrum.min() + 1e-12)

        # Registrar no histórico
        self.spectrum_history.append(phi_c_spectrum.clone())

        return phi_c_spectrum

    def _estimate_eigenvalues_lanczos(self, data: torch.Tensor,
                                     num_eigenvalues: int) -> torch.Tensor:
        """
        Estima autovalores de menor magnitude via Lanczos em batch.
        Simplificação: usar SVD truncado como proxy para demonstração.
        """
        # Em produção: implementar Lanczos verdadeiro com re-ortogonalização
        # Aqui: SVD truncado como aproximação eficiente
        U, S, Vh = torch.linalg.svd(data, full_matrices=False)

        # Retornar valores singulares como proxy para |autovalores|
        return S[:num_eigenvalues]

    def is_local_peak(self, current_spectrum: torch.Tensor) -> bool:
        """Detecta se espectro atual é pico local no histórico."""
        if len(self.spectrum_history) < self.peak_detection_window:
            return False

        # Calcular média do espectro (proxy para "altura" do pico)
        current_mean = current_spectrum.mean().item()
        recent_means = [spec.mean().item() for spec in
                       list(self.spectrum_history)[-self.peak_detection_window:]]

        # Verificar se atual é significativamente maior que recentes
        recent_avg = np.mean(recent_means[:-1]) if len(recent_means) > 1 else current_mean
        return current_mean > recent_avg * self.peak_threshold_ratio

    def get_confidence(self) -> float:
        """Retorna confiança na estimativa de Φ_C baseada em estabilidade histórica."""
        if len(self.spectrum_history) < 5:
            return 0.5

        # Calcular variância do espectro médio no histórico recente
        recent = list(self.spectrum_history)[-10:]
        means = [spec.mean().item() for spec in recent]
        variance = np.var(means)

        # Confiança inversamente proporcional à variância
        return 1.0 / (1.0 + 10.0 * variance)

    def get_current_spectrum(self) -> torch.Tensor:
        """Retorna espectro de coerência mais recente."""
        return self.spectrum_history[-1].clone() if self.spectrum_history else torch.zeros(self.num_scales)
