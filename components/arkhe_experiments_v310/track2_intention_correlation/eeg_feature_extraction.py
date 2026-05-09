#!/usr/bin/env python3
"""
track2_intention_correlation/eeg_feature_extraction.py
Extrai features de "intenção" a partir de sinal EEG para correlação com sincronização.
"""
import numpy as np
from scipy import signal, stats
from typing import Dict, List, Optional

class EEGIntentionExtractor:
    """Extrai métricas de intenção cognitiva a partir de sinal EEG multicanal."""

    def __init__(self, sampling_rate_hz: float = 250.0,
                 bands: Dict[str, tuple] = None):
        self.fs = sampling_rate_hz
        # Bandas de frequência padrão (Hz)
        self.bands = bands or {
            'theta': (4, 8),
            'alpha': (8, 13),
            'beta': (13, 30),
            'gamma': (30, 50)
        }

    def compute_band_power(self, eeg_signal: np.ndarray,
                          band: tuple) -> np.ndarray:
        """Calcula potência espectral em banda específica via Welch."""
        f, Pxx = signal.welch(eeg_signal, fs=self.fs, nperseg=256)
        mask = (f >= band[0]) & (f <= band[1])
        return np.trapz(Pxx[mask], f[mask])

    def extract_intention_features(self, eeg_data: np.ndarray,
                                  channels: List[str] = None) -> Dict:
        """
        Extrai features de intenção para uma janela de EEG.
        """
        if channels is None:
            channels = ['F3', 'F4', 'C3', 'C4', 'P3', 'P4']  # Padrão 10-20

        features = {}

        # 1. Potência gamma média (proxy para intenção focada)
        gamma_powers = [self.compute_band_power(eeg_data[:, ch], self.bands['gamma'])
                       for ch in range(eeg_data.shape[1])]
        features['gamma_power_mean'] = float(np.mean(gamma_powers))
        features['gamma_power_std'] = float(np.std(gamma_powers))

        # 2. Supressão alpha (alpha_baseline - alpha_active)
        # Assume primeira metade como baseline, segunda como ativa
        mid = len(eeg_data) // 2
        alpha_base = np.mean([self.compute_band_power(eeg_data[:mid, ch], self.bands['alpha'])
                             for ch in range(eeg_data.shape[1])])
        alpha_active = np.mean([self.compute_band_power(eeg_data[mid:, ch], self.bands['alpha'])
                               for ch in range(eeg_data.shape[1])])
        features['alpha_suppression'] = float(alpha_base - alpha_active)

        # 3. Coerência inter-hemisférica (F3-F4, C3-C4, P3-P4)
        coherences = []
        pairs = [(0, 1), (2, 3), (4, 5)] if len(channels) >= 6 else [(0, 1)]
        for i, j in pairs:
            if i < eeg_data.shape[1] and j < eeg_data.shape[1]:
                f, Cxy = signal.coherence(eeg_data[:, i], eeg_data[:, j], fs=self.fs)
                # Média na banda gamma
                mask = (f >= self.bands['gamma'][0]) & (f <= self.bands['gamma'][1])
                coherences.append(np.mean(Cxy[mask]))
        features['inter_hemispheric_coherence_gamma'] = float(np.mean(coherences)) if coherences else 0.0

        # 4. Dimensão fractal (Higuchi) como proxy de complexidade cognitiva
        features['fractal_dimension'] = float(self._higuchi_fd(eeg_data.mean(axis=1), k_max=10))

        # Feature composta de "intenção" (combinação ponderada)
        features['intention_score'] = float(
            0.4 * features['gamma_power_mean'] +
            0.3 * features['alpha_suppression'] +
            0.2 * features['inter_hemispheric_coherence_gamma'] +
            0.1 * features['fractal_dimension']
        )

        return features

    def _higuchi_fd(self, x: np.ndarray, k_max: int = 10) -> float:
        """Calcula dimensão fractal via método de Higuchi (simplificado)."""
        N = len(x)
        Lk = []
        for k in range(1, k_max + 1):
            Lmk = []
            for m in range(1, k + 1):
                x_m = x[m-1::k]
                Lmk_val = (np.sum(np.abs(np.diff(x_m))) * (N - 1) /
                          (k * len(x_m) * (len(x_m) - 1)))
                Lmk.append(Lmk_val)
            Lk.append(np.mean(Lmk))

        # Regressão linear em log-log
        ks = np.arange(1, k_max + 1)
        with np.errstate(divide='ignore', invalid='ignore'):
            log_Lk = np.log(Lk)
            log_k = np.log(1 / ks)

        # Remover NaNs
        valid = ~(np.isnan(log_Lk) | np.isnan(log_k))
        if np.sum(valid) < 3:
            return np.nan

        slope, _, _, _, _ = stats.linregress(log_k[valid], log_Lk[valid])
        return -slope if not np.isnan(slope) else np.nan
