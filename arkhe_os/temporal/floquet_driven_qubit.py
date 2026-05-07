# arkhe_os/temporal/floquet_driven_qubit.py — Versão Canônica v280.1
import numpy as np
from dataclasses import dataclass
from typing import Optional, Callable

@dataclass
class FloquetParameters:
    """Parâmetros de driving de Floquet para estabilização quântica."""
    omega_d: float          # Frequência de driving [rad/s]
    omega_R: float          # Frequência de Rabi [rad/s]
    phase_offset: float = 0.0  # Fase inicial do driving
    envelope: Optional[Callable[[float], float]] = None  # Envelope temporal

    def instantaneous_coupling(self, t: float) -> float:
        """Acoplamento efetivo no tempo t, com envelope opcional."""
        base = self.omega_R * np.cos(self.omega_d * t + self.phase_offset)
        if self.envelope:
            return base * self.envelope(t)
        return base

class FloquetStabilizedQubit:
    """
    Qubit temporal com estabilização por driving de Floquet.

    Princípio fundamental:
    'Não mude o material — mude o tempo.
     Não lute contra a decoerência — dance com ela.'
    """
    def __init__(self, params: FloquetParameters, gamma_0: float = 1.0):
        self.params = params
        self.gamma_0 = gamma_0  # Taxa de decoerência intrínseca
        self.T = 2 * np.pi / params.omega_d  # Período de Floquet

    def effective_decoherence_rate(self, averaging_window: Optional[float] = None) -> float:
        """
        γ_eff = γ_0 * exp(-⟨Ω_R²⟩/ω_d²)

        Se averaging_window fornecido, calcula média temporal do acoplamento.
        """
        if averaging_window is None:
            # Média sobre um período completo de Floquet
            omega_R_eff = self.params.omega_R / np.sqrt(2)  # RMS de cos(ωt)
        else:
            # Média numérica sobre janela específica
            ts = np.linspace(0, averaging_window, 1000)
            couplings = [self.params.instantaneous_coupling(t) for t in ts]
            omega_R_eff = np.sqrt(np.mean(np.array(couplings)**2))

        # NOTE: the formula in doc is γ_0 * exp(-Ω_R²/ω_d²) or something similar
        # Implementation is using exp(-(omega_R_eff**2) / (self.params.omega_d**2))
        return self.gamma_0 * np.exp(-(omega_R_eff**2) / (self.params.omega_d**2))

    def coherence_time(self, confidence: float = 0.95) -> float:
        """
        T_2 com fator de confiança estatística.
        Para sistemas de Floquet, a coerência é periódica —
        retornamos o tempo até a primeira revivificação significativa.
        """
        gamma_eff = self.effective_decoherence_rate()
        if gamma_eff < 1e-12:
            return float('inf')  # Coerência efetivamente preservada

        # Tempo para decaimento a (1-confidence) da amplitude inicial
        return -np.log(1 - confidence) / gamma_eff

    def stability_gain(self) -> float:
        gamma_eff = self.effective_decoherence_rate()
        return self.gamma_0 / gamma_eff if gamma_eff > 0 else float('inf')

    def floquet_quasienergy_spectrum(self, n_harmonics: int = 5) -> np.ndarray:
        """
        Calcula o espectro de quasi-energias de Floquet:
        ε_n = ε_0 + n·ℏω_d (mod ℏω_d)

        Retorna as n_harmonics primeiras quasi-energias normalizadas.
        """
        # Em aproximação de rotating wave approximation (RWA)
        epsilon_0 = -self.params.omega_R**2 / (4 * self.params.omega_d)
        harmonics = np.arange(-n_harmonics, n_harmonics + 1)
        return epsilon_0 + harmonics * self.params.omega_d

    def stability_phase_diagram(self, omega_d_range, omega_R_range) -> np.ndarray:
        """
        Gera diagrama de fase de estabilidade: ganho de T_2 em função
        dos parâmetros de driving.
        """
        gains = np.zeros((len(omega_d_range), len(omega_R_range)))
        for i, wd in enumerate(omega_d_range):
            for j, wR in enumerate(omega_R_range):
                params = FloquetParameters(omega_d=wd, omega_R=wR)
                qubit = FloquetStabilizedQubit(params, self.gamma_0)
                gains[i, j] = qubit.effective_decoherence_rate() / self.gamma_0
        return 1 / gains  # Fator de melhoria em T_2

    def stability_gain(self) -> float:
        """
        Retorna o ganho de estabilidade T_2.
        Helper para retornar fator de melhoria em T_2 diretamente: γ_0 / γ_eff
        """
        gamma_eff = self.effective_decoherence_rate()
        if gamma_eff == 0:
        """Retorna o ganho em T_2 (γ_0 / γ_eff)."""
        gamma_eff = self.effective_decoherence_rate()
        if gamma_eff < 1e-12:
            return float('inf')
        return self.gamma_0 / gamma_eff
