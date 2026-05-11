#!/usr/bin/env python3
"""
hyperbolic_qp_recombination.py — Modelo da cinética hiperbólica de recombinação de quasipartículas.
Implementa δf_q(t) = δf₀/(1+t/t_rec) e cálculo do tempo crítico de echo.
"""

import numpy as np
from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class QPRecombinationParams:
    """Parâmetros do modelo de recombinação de QPs."""
    delta_f0_MHz: float  # Deslocamento inicial de frequência (MHz)
    t_rec_ms: float      # Tempo de recombinação característico (ms)
    temperature_mK: float = 20.0  # Temperatura do qubit (mK)
    material: str = 'aluminum'    # Material supercondutor

class HyperbolicQPRecombinationModel:
    """
    Modelo da cinética hiperbólica de recombinação de quasipartículas.

    Baseado em Kurilovich et al., Phys. Rev. X 16, 021025 (2026)
    """

    def __init__(self, params: QPRecombinationParams):
        self.params = params

    def frequency_shift(self, time_ns: float) -> float:
        """
        Calcula deslocamento de frequência no tempo t.

        δf_q(t) = δf₀ / (1 + t/t_rec)

        Args:
            time_ns: tempo em nanosegundos após o impacto

        Returns:
            Deslocamento de frequência em MHz
        """
        t_ms = time_ns * 1e-6  # ns → ms
        return self.params.delta_f0_MHz / (1.0 + t_ms / self.params.t_rec_ms)

    def accumulated_phase_error(self, duration_ns: float) -> float:
        """
        Calcula erro de fase acumulado durante um intervalo.

        δφ(T) = 2π·δf₀·t_rec·ln(1 + T/t_rec)

        Args:
            duration_ns: duração do intervalo em nanosegundos

        Returns:
            Erro de fase acumulado em radianos
        """
        T_ms = duration_ns * 1e-6
        delta_f0_Hz = self.params.delta_f0_MHz * 1e6
        t_rec_s = self.params.t_rec_ms * 1e-3

        return 2 * np.pi * delta_f0_Hz * t_rec_s * np.log(1.0 + T_ms / self.params.t_rec_ms)

    def compute_critical_echo_time(self, max_phase_rad: float = np.pi) -> float:
        """
        Calcula tempo crítico para aplicação de spin-echo.

        Resolve: δφ(T_crit) = max_phase_rad
        T_crit = t_rec · (exp(max_phase/(2π·δf₀·t_rec)) - 1)

        Args:
            max_phase_rad: fase máxima tolerável antes do echo (radianos)

        Returns:
            Tempo crítico em nanosegundos
        """
        delta_f0_Hz = self.params.delta_f0_MHz * 1e6
        t_rec_s = self.params.t_rec_ms * 1e-3

        # Resolver equação transcendental
        exponent = max_phase_rad / (2 * np.pi * delta_f0_Hz * t_rec_s)
        T_crit_s = t_rec_s * (np.exp(exponent) - 1)

        return T_crit_s * 1e9  # Converter para ns

    def is_echo_needed(self, elapsed_time_ns: float, current_phase_rad: float) -> bool:
        """
        Decide se spin-echo deve ser aplicado baseado no estado atual.

        Critério: aplicar echo se fase acumulada > 0.8·π (margem de segurança)
        """
        safety_threshold = 0.8 * np.pi
        return current_phase_rad >= safety_threshold

    def simulate_burst_evolution(
        self,
        total_time_ns: float,
        time_step_ns: float = 10.0,
        apply_echo_at: Optional[float] = None
    ) -> Dict[str, np.ndarray]:
        """
        Simula evolução completa de um burst de QPs.

        Returns:
            Dict com arrays de tempo, frequency_shift, accumulated_phase
        """
        times = np.arange(0, total_time_ns + time_step_ns, time_step_ns)
        freq_shifts = np.array([self.frequency_shift(t) for t in times])

        # Calcular fase acumulada com possível aplicação de echo
        phases = np.zeros_like(times)
        for i, t in enumerate(times):
            if apply_echo_at and t >= apply_echo_at:
                # Após echo: fase é "resetada" parcialmente
                # Simplificação: fase acumulada até echo, depois nova acumulação
                if t == apply_echo_at:
                    phases[i] = self.accumulated_phase_error(apply_echo_at)
                else:
                    # Nova acumulação após echo
                    elapsed_post_echo = t - apply_echo_at
                    phases[i] = phases[i-1] + self.accumulated_phase_error(elapsed_post_echo) * 0.1  # Echo reduz efeito
            else:
                phases[i] = self.accumulated_phase_error(t)

        return {
            'time_ns': times,
            'frequency_shift_MHz': freq_shifts,
            'accumulated_phase_rad': phases,
            'critical_echo_time_ns': self.compute_critical_echo_time()
        }

    def estimate_t_rec_from_data(
        self,
        time_measurements: np.ndarray,
        frequency_measurements: np.ndarray
    ) -> float:
        """
        Estima t_rec a partir de dados experimentais via fit não-linear.

        Modelo: δf(t) = δf₀ / (1 + t/t_rec)
        """
        from scipy.optimize import curve_fit

        def hyperbolic_model(t, delta_f0, t_rec):
            return delta_f0 / (1.0 + t / t_rec)

        # Converter tempo para ms para estabilidade numérica
        t_ms = time_measurements * 1e-6

        # Fit não-linear
        popt, _ = curve_fit(
            hyperbolic_model,
            t_ms,
            frequency_measurements,
            p0=[self.params.delta_f0_MHz, self.params.t_rec_ms],
            bounds=([0, 0], [100, 100])  # Limites físicos
        )

        return popt[1]  # t_rec estimado em ms
