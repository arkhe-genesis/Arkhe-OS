# arkhe_optica/photon_sorter_simulator.py
"""
Simulador de alta fidelidade do Photon Sorter baseado nas equações input-output
de Nielsen et al. (Phys. Rev. Lett. 2026).
"""

import torch
import torch.nn as nn
import numpy as np
from typing import Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class PhotonSorterConfig:
    """Parâmetros físicos do Photon Sorter"""
    # Ponto quântico
    qd_transition_freq_THz: float = 280.0  # ~1064 nm
    qd_decay_rate_GHz: float = 1.0  # γ/2π
    qd_dephasing_rate_GHz: float = 0.1  # γ_d/2π

    # Cavidade MZI
    cavity_length_um: float = 10.0
    waveguide_loss_dB_per_cm: float = 0.5
    coupling_efficiency: float = 0.9  # β

    # Interferômetro
    mzi_phase_offset_rad: float = 0.0
    mzi_imbalance: float = 0.01  # Diferença de caminho

    # Detectores
    detector_efficiency: float = 0.95
    dark_count_rate_Hz: float = 100.0

    # Simulação
    n_time_steps: int = 1000
    dt_ps: float = 0.1  # Passo temporal em picosegundos


class PhotonSorterHighFidelity(nn.Module):
    """
    Simulador input-output completo do Photon Sorter.
    Implementa as equações de Heisenberg-Langevin para ponto quântico acoplado a MZI.
    """

    def __init__(self, config: PhotonSorterConfig):
        super().__init__()
        self.cfg = config

        # Constantes físicas
        self.hbar = 1.054571817e-34  # J·s
        self.c = 299792458.0  # m/s

        # Parâmetros derivados
        self.omega_qd = 2 * np.pi * config.qd_transition_freq_THz * 1e12  # rad/s
        self.gamma = 2 * np.pi * config.qd_decay_rate_GHz * 1e9  # rad/s
        self.gamma_d = 2 * np.pi * config.qd_dephasing_rate_GHz * 1e9  # rad/s
        self.beta = config.coupling_efficiency

    def simulate_input_output(
        self,
        input_state: str = "coherent",  # "coherent", "fock_1", "fock_2", "thermal"
        input_amplitude: float = 0.1,  # Para estados coerentes
        n_photons: int = 1,  # Para estados de Fock
        thermal_mean_n: float = 0.5,  # Para estados térmicos
        mzi_phase: float = 0.0  # Fase adicional do MZI
    ) -> Dict:
        """
        Simula resposta do Photon Sorter para diferentes estados de entrada.

        Returns:
            Dict com probabilidades de detecção nas saídas superior/inferior
        """
        # Gerar campo de entrada estocástico
        input_field = self._generate_input_field(
            input_state, input_amplitude, n_photons, thermal_mean_n
        )

        # Resolver equações de Heisenberg-Langevin via Euler-Maruyama
        output_upper, output_lower = self._solve_langevin(input_field, mzi_phase)

        # Calcular estatísticas de detecção
        stats = self._compute_detection_stats(output_upper, output_lower)

        return {
            'input_state': input_state,
            'output_probabilities': stats,
            'sorting_fidelity': self._compute_sorting_fidelity(stats, input_state),
            'bsm_success_prob': self._compute_bsm_probability(stats)
        }

    def _generate_input_field(
        self, state_type: str, amplitude: float, n_photons: int, thermal_n: float
    ) -> torch.Tensor:
        """Gera campo de entrada estocástico conforme tipo de estado"""
        n_steps = self.cfg.n_time_steps
        dt = self.cfg.dt_ps * 1e-12  # Converter para segundos

        if state_type == "coherent":
            # Estado coerente: campo clássico + ruído quântico
            field = torch.zeros(n_steps, dtype=torch.complex64)
            field += amplitude  # Amplitude constante
            # Adicionar ruído de vácuo
            field += torch.randn(n_steps, dtype=torch.float32).to(torch.complex64) * np.sqrt(self.gamma * dt)
            field += 1j * torch.randn(n_steps, dtype=torch.float32).to(torch.complex64) * np.sqrt(self.gamma * dt)

        elif state_type.startswith("fock"):
            # Estado de Fock: simular via trajetórias quânticas (simplificado)
            # Para |1⟩: um pulso gaussiano com área normalizada
            t = torch.arange(n_steps) * dt * 1e12  # em ps
            pulse_center = n_steps // 2
            pulse_width = 10.0  # ps
            envelope = torch.exp(-0.5 * ((t - pulse_center) / pulse_width)**2).to(torch.complex64)

            if state_type == "fock_1":
                # |1⟩: campo com flutuações quânticas
                field = envelope * (1.0 + 0.1 * (torch.randn(n_steps) + 1j * torch.randn(n_steps)).to(torch.complex64))
            elif state_type == "fock_2":
                # |2⟩: amplitude maior, estatísticas diferentes
                field = envelope * np.sqrt(2) * (1.0 + 0.1 * (torch.randn(n_steps) + 1j * torch.randn(n_steps)).to(torch.complex64))
            else:
                field = torch.zeros(n_steps, dtype=torch.complex64)

        elif state_type == "thermal":
            # Estado térmico: distribuição de Bose-Einstein
            field = torch.zeros(n_steps, dtype=torch.complex64)
            for _ in range(int(thermal_n * 10)):  # Amostragem de fótons térmicos
                phase = torch.rand(1) * 2 * np.pi
                field += torch.exp(1j * phase) * torch.randn(n_steps).to(torch.complex64) * np.sqrt(self.gamma * dt)
        else:
            field = torch.zeros(n_steps, dtype=torch.complex64)

        return field

    def _solve_langevin(
        self,
        input_field: torch.Tensor,
        mzi_phase: float
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Resolve equações de Heisenberg-Langevin para o sistema QD+MZI.

        Equações (simplificadas de Nielsen et al.):
        dσ⁻/dt = -(γ/2 + γ_d + iΔ)σ⁻ + i√γ β a_in σ_z + noise
        a_out = a_in + i√γ β σ⁻

        MZI: interfere a_out de dois braços com fase relativa
        """
        n_steps = len(input_field)
        dt = self.cfg.dt_ps * 1e-12

        # Inicializar operadores
        sigma_minus = torch.zeros(n_steps, dtype=torch.complex64)  # Operador de descida do QD
        sigma_z = torch.ones(n_steps) * (-1.0)  # Inicialmente no estado fundamental

        # Propagação temporal via Euler-Maruyama
        for t in range(1, n_steps):
            # Detuning (assumir ressonância para simplificar)
            delta = 0.0

            # Termo de ruído quântico (simulado)
            noise_real = torch.randn(1) * np.sqrt(self.gamma * dt)
            noise_imag = torch.randn(1) * np.sqrt(self.gamma * dt)
            noise = noise_real + 1j * noise_imag

            # Equação para σ⁻
            d_sigma = (
                -(self.gamma/2 + self.gamma_d + 1j*delta) * sigma_minus[t-1] +
                1j * np.sqrt(self.gamma) * self.beta * input_field[t-1] * sigma_z[t-1] +
                noise.to(torch.complex64)
            )
            sigma_minus[t] = sigma_minus[t-1] + d_sigma * dt

            # Atualizar σ_z (conservação de população, simplificado)
            sigma_z[t] = torch.clamp(sigma_z[t-1] - 2 * torch.abs(d_sigma).to(torch.float32)**2 * dt, -1, 1)

        # Campo de saída do braço com QD
        a_out_qd = input_field + 1j * np.sqrt(self.gamma) * self.beta * sigma_minus

        # Campo de saída do braço de referência (sem QD, apenas atraso)
        a_out_ref = torch.roll(input_field, shifts=int(self.cfg.cavity_length_um * 1000 // 300))  # Atraso ~3.3 fs/μm

        # Interferência no MZI com fase adicional
        phase_factor = torch.exp(1j * torch.tensor(mzi_phase + self.cfg.mzi_phase_offset_rad))

        # Saídas do MZI (matriz de transferência 50:50 com fase)
        output_upper = (a_out_qd + phase_factor * a_out_ref) / np.sqrt(2)
        output_lower = (a_out_qd - phase_factor * a_out_ref) / np.sqrt(2)

        return output_upper, output_lower

    def _compute_detection_stats(
        self,
        output_upper: torch.Tensor,
        output_lower: torch.Tensor
    ) -> Dict:
        """Calcula probabilidades de detecção nas saídas"""
        # Intensidade integrada (número esperado de fótons)
        n_upper = torch.mean(torch.abs(output_upper)**2).item()
        n_lower = torch.mean(torch.abs(output_lower)**2).item()
        n_total = n_upper + n_lower

        # Probabilidades normalizadas
        p_upper = n_upper / (n_total + 1e-10)
        p_lower = n_lower / (n_total + 1e-10)

        # Correlações de segunda ordem (g²) para discriminação de estados
        g2_upper = self._compute_g2(output_upper)
        g2_lower = self._compute_g2(output_lower)

        return {
            'p_upper': float(p_upper),
            'p_lower': float(p_lower),
            'n_total': float(n_total),
            'g2_upper': float(g2_upper),
            'g2_lower': float(g2_lower)
        }

    def _compute_g2(self, field: torch.Tensor) -> float:
        """Calcula função de correlação de segunda ordem g²(0)"""
        intensity = torch.abs(field)**2
        if torch.mean(intensity) < 1e-10:
            return 2.0  # Valor padrão para campo fraco

        # g²(0) = ⟨:n²:⟩ / ⟨n⟩² ≈ ⟨I²⟩ / ⟨I⟩² para detecção direta
        g2 = torch.mean(intensity**2) / (torch.mean(intensity)**2 + 1e-10)
        return float(torch.clamp(g2, 0, 2))

    def _compute_sorting_fidelity(self, stats: Dict, input_state: str) -> float:
        """Calcula fidelidade de sorting para o estado de entrada"""
        if input_state == "fock_1":
            # Para |1⟩, queremos detecção na saída superior
            return stats['p_upper']
        elif input_state == "fock_2":
            # Para |2⟩, queremos detecção na saída inferior (não-linearidade)
            return stats['p_lower']
        else:
            # Para outros estados, fidelidade = max(p_upper, p_lower)
            return max(stats['p_upper'], stats['p_lower'])

    def _compute_bsm_probability(self, stats: Dict) -> float:
        """Calcula probabilidade de sucesso em Bell State Measurement"""
        # BSM requer detecção coincidente com correlações específicas
        # Simplificado: usar produto das probabilidades e g²
        return stats['p_upper'] * stats['p_lower'] * (2 - stats['g2_upper']) * 0.5
