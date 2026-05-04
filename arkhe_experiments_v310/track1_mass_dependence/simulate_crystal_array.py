#!/usr/bin/env python3
"""
track1_mass_dependence/simulate_crystal_array.py
Simula array de cristais piezoelétricos com acoplamento Kuramoto + ruído quântico.
"""
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class CrystalArraySpec:
    """Especificação do array de cristais para teste de massa-dependência."""
    n_crystals: int  # Número de cristais (16, 64, 256, 768)
    coupling_strength: float = 0.618  # κ = φ⁻¹
    natural_freq_hz: float = 32768.0  # Frequência natural dos cristais
    noise_amplitude: float = 0.01  # Amplitude do ruído de fase
    dt: float = 0.001  # Passo de integração (s)
    max_time_s: float = 10.0  # Tempo máximo de simulação

class CrystalArraySimulator:
    """Simula dinâmica de fase de array de cristais acoplados."""

    def __init__(self, spec: CrystalArraySpec):
        self.spec = spec
        self.n = spec.n_crystals
        self.rng = np.random.default_rng(42)  # Reprodutibilidade

    def initialize_phases(self, coherence_target: float = 0.3):
        """Inicializa fases com coerência parcial (estado pré-colapso)."""
        # Fases concentradas em torno de SYNC_PHASE com dispersão controlada
        sync_phase = 0.58 * np.pi
        dispersion = np.arccos(2 * coherence_target - 1)
        phases = self.rng.vonmises(sync_phase, 1/dispersion, self.n)
        return phases % (2 * np.pi)

    def kuramoto_step(self, phases: np.ndarray, intention_signal: float = 0.0) -> np.ndarray:
        """Um passo de integração da equação de Kuramoto com intenção."""
        # Termo de acoplamento Kuramoto
        mean_field = np.mean(np.exp(1j * phases))
        coupling_term = self.spec.coupling_strength * np.imag(
            mean_field * np.exp(-1j * phases)
        )

        # Termo de intenção (modulação do campo Chrono‑Coil)
        sync_phase = 0.58 * np.pi
        intention_term = intention_signal * 0.05 * np.cos(phases - sync_phase)

        # Ruído de fase (decoerência ambiental)
        noise = self.rng.normal(0, self.spec.noise_amplitude, self.n)

        # Atualização de fase (Euler-Maruyama)
        dphases = (coupling_term + intention_term + noise) * self.spec.dt
        return (phases + dphases) % (2 * np.pi)

    def compute_order_parameter(self, phases: np.ndarray) -> float:
        """Calcula parâmetro de ordem de Kuramoto (coerência global)."""
        return float(np.abs(np.mean(np.exp(1j * phases))))

    def run_until_synchronization(self, threshold: float = 0.95,
                                  intention_signal: float = 0.85) -> Dict:
        """Executa simulação até atingir sincronização ou tempo máximo."""
        phases = self.initialize_phases()
        t = 0.0
        sync_time = None

        while t < self.spec.max_time_s:
            # Calcular coerência atual
            coherence = self.compute_order_parameter(phases)

            # Verificar critério de sincronização
            if coherence >= threshold and sync_time is None:
                sync_time = t

            # Avançar um passo
            phases = self.kuramoto_step(phases, intention_signal)
            t += self.spec.dt

        return {
            'n_crystals': self.n,
            'sync_time_s': float(sync_time) if sync_time is not None else None,
            'final_coherence': float(self.compute_order_parameter(phases)),
            'threshold': threshold,
            'intention_signal': intention_signal
        }
