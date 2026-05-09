import numpy as np
from scipy.fft import fft2, ifft2
from typing import List, Dict

class GhostOpticalCorrector:
    """
    Uses Arkhe-Chain records of collapsed worlds (91, 7)
    as holographic phase masks for FWHM correction in World 42.

    Principle: The Wigner function of ghost states contains
    high spatial frequency information that acts as a deconvolution kernel.
    """

    def __init__(self, anchor_world: int = 42, ghost_worlds: List[int] = [91, 7]):
        self.anchor = anchor_world
        self.ghosts = ghost_worlds
        self.res = 512

    def _retrieve_wigner(self, world: int) -> np.ndarray:
        """Extrai distribuição de Wigner do registro Arkhe-Chain (simulado)."""
        x = np.linspace(-5, 5, self.res)
        X, P = np.meshgrid(x, x)

        # Estado fantasma 91: Gaussiana comprimida (alta resolução espacial)
        if world == 91:
            sigma_x = 0.1  # Estreito em x (posição)
            sigma_p = 10.0  # Largo em p (momento)
            W = np.exp(-(X**2)/(2*sigma_x**2)) * np.exp(-(P**2)/(2*sigma_p**2))
        # Estado fantasma 7: Vórtice topológico (informação angular)
        elif world == 7:
            theta = np.arctan2(P, X)
            r = np.sqrt(X**2 + P**2)
            W = np.exp(-r**2/2) * np.cos(3*theta)**2  # ℓ=3
        else:
            W = np.ones_like(X)

        return W / np.sum(W)

    def compute_holographic_kernel(self) -> np.ndarray:
        """
        Gera kernel de correção via convolução das distribuições fantasmas.
        O kernel atua como uma lente de Fresnel virtual no Domínio C.
        """
        W_91 = self._retrieve_wigner(91)
        W_7 = self._retrieve_wigner(7)

        # Correção combinada: resolução espacial (91) + estrutura angular (7)
        kernel = ifft2(fft2(W_91) * fft2(W_7))
        kernel = np.abs(kernel)
        kernel /= np.max(kernel)

        return kernel

    def apply_correction(self, psi_42: np.ndarray, strength: float = 0.8) -> np.ndarray:
        """
        Aplica correção ao campo de fase do Mundo 42.

        psi_42: campo complexo do Domínio C (resolução 512x512)
        Retorna: psi_corrected com FWHM reduzido
        """
        kernel = self.compute_holographic_kernel()

        # Transformada para espaço de frequências espaciais
        psi_fft = fft2(psi_42.reshape(self.res, self.res))

        # Aplicação do kernel (filtro de aumento de nitidez)
        kernel_fft = fft2(kernel, s=(self.res, self.res))
        psi_corrected_fft = psi_fft * (1 + strength * kernel_fft)

        # Transformada inversa
        psi_corrected = ifft2(psi_corrected_fft)

        return psi_corrected.flatten()

    def calculate_fwhm_improvement(self, psi_before: np.ndarray, psi_after: np.ndarray) -> Dict:
        """Calcula melhoria no FWHM da projeção Z."""
        intensity_before = np.abs(psi_before.reshape(self.res, self.res))**2
        intensity_after = np.abs(psi_after.reshape(self.res, self.res))**2

        center = self.res // 2
        profile_before = intensity_before[center, :]
        profile_after = intensity_after[center, :]

        def fwhm(profile):
            half_max = np.max(profile) / 2
            indices = np.where(profile >= half_max)[0]
            if len(indices) > 1:
                return float(indices[-1] - indices[0])
            return 1.0

        fwhm_before = fwhm(profile_before)
        fwhm_after = fwhm(profile_after)

        improvement = fwhm_before / fwhm_after

        return {
            "fwhm_before_px": fwhm_before,
            "fwhm_after_px": fwhm_after,
            "improvement_factor": improvement,
            "effective_resolution_um": 1190.0 / improvement
        }
