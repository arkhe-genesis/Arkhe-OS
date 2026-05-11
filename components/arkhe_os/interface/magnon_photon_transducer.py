#!/usr/bin/env python3
"""
magnon_photon_transducer.py — Interface magnon-fóton para entrada/saída clássica.
Implementa transdução coerente entre excitações magnônicas (quântico) e fótons (clássico/óptico).
"""

import numpy as np
import torch
from typing import Dict, List, Optional, Tuple, Callable, Any, Union
from dataclasses import dataclass, field
from enum import Enum, auto
import time
import hashlib

class TransductionDirection(Enum):
    """Direção da transdução."""
    MAGNON_TO_PHOTON = auto()  # Leitura: magnon → fóton (saída clássica)
    PHOTON_TO_MAGNON = auto()  # Escrita: fóton → magnon (entrada clássica)
    BIDIRECTIONAL = auto()     # Ambos os sentidos

class CouplingRegime(Enum):
    """Regime de acoplamento magnon-fóton."""
    WEAK = auto()        # g < κ, γ: acoplamento perturbativo
    STRONG = auto()      # g > κ, γ: oscilações de Rabi resolvíveis
    CRITICAL = auto()    # g ≈ (κ + γ)/4: ponto ótimo para transdução
    ULTRA_STRONG = auto() # g > ω: regime beyond-RWA

@dataclass
class TransducerConfig:
    """Configuração do transdutor magnon-fóton."""
    # Parâmetros do modo magnônico
    magnon_frequency_ghz: float = 10.0
    magnon_linewidth_mhz: float = 1.0  # γ/2π
    magnon_mode_volume: float = 1e-15  # m³

    # Parâmetros do modo fotônico
    photon_frequency_ghz: float = 10.0  # Ressonante com magnon
    photon_linewidth_mhz: float = 5.0   # κ/2π
    photon_mode_volume: float = 1e-12   # m³ (cavidade óptica)

    # Acoplamento
    coupling_strength_mhz: float = 2.0  # g/2π
    coupling_regime: CouplingRegime = CouplingRegime.CRITICAL

    # Parâmetros operacionais
    temperature_k: float = 4.2  # Criogênico para baixo ruído térmico
    drive_power_dbm: float = -20.0  # Potência de drive para transdução
    impedance_match: bool = True  # Casamento de impedância para máxima eficiência

    # Direção de operação
    direction: TransductionDirection = TransductionDirection.BIDIRECTIONAL

@dataclass
class TransductionResult:
    """Resultado de uma operação de transdução."""
    success: bool
    input_type: str  # 'magnon' or 'photon'
    output_type: str
    input_energy: float  # Em unidades de ℏω
    output_energy: float
    efficiency: float  # η = P_out / P_in
    added_noise_photons: float  # Ruído adicionado em unidades de fótons
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def signal_to_noise_ratio(self) -> float:
        """Calcula SNR da transdução."""
        if self.added_noise_photons < 1e-10:
            return float('inf')
        return self.output_energy / self.added_noise_photons

class MagnonPhotonTransducer:
    """
    Interface magnon-fóton para entrada/saída clássica da Renda Neural.

    Física base: Hamiltoniano de Jaynes-Cummings generalizado
    H = ℏω_m a†a + ℏω_c b†b + ℏg(a†b + ab†) + H_drive + H_diss

    Onde:
    - a, a†: operadores magnônicos
    - b, b†: operadores fotônicos
    - g: acoplamento magnon-fóton
    - H_drive: drive clássico para transdução
    - H_diss: dissipação (κ para fótons, γ para magnons)
    """

    def __init__(self, config: TransducerConfig, node_id: Optional[str] = None):
        self.config = config
        self.node_id = node_id or f"transducer_{hashlib.sha256(str(time.time()).encode()).hexdigest()[:8]}"

        # Calcular parâmetros derivados
        self._compute_derived_parameters()

        # Estado interno
        self.magnon_occupation: float = 0.0  # ⟨a†a⟩
        self.photon_occupation: float = 0.0   # ⟨b†b⟩
        self.coherence: complex = 0.0 + 0.0j  # ⟨a†b⟩ (coerência magnon-fóton)

        # Métricas de transdução
        self.transduction_metrics = {
            'operations_count': 0,
            'avg_efficiency': 0.0,
            'avg_added_noise': 0.0,
            'successful_transductions': 0,
            'failed_transductions': 0
        }

        # Callbacks para eventos de transdução
        self.transduction_callbacks: List[Callable] = []

        print(f"🔬 MagnonPhotonTransducer initialized: {self.node_id}")
        print(f"   Regime: {config.coupling_regime.name}, g/2π = {config.coupling_strength_mhz}MHz")

    def _compute_derived_parameters(self):
        """Calcula parâmetros derivados da configuração."""
        # Converter para rad/s
        self.ω_m = self.config.magnon_frequency_ghz * 2 * np.pi * 1e9
        self.ω_c = self.config.photon_frequency_ghz * 2 * np.pi * 1e9
        self.γ = self.config.magnon_linewidth_mhz * 2 * np.pi * 1e6  # Taxa de decaimento magnon
        self.κ = self.config.photon_linewidth_mhz * 2 * np.pi * 1e6      # Taxa de decaimento fóton
        self.g = self.config.coupling_strength_mhz * 2 * np.pi * 1e6  # Acoplamento

        # Detuning
        self.Δ = self.ω_m - self.ω_c

        # Cooperativity: figura de mérito para transdução
        # C = 4g²/(κγ) — C > 1 necessário para transdução eficiente
        self.cooperativity = 4 * self.g**2 / (self.κ * self.γ)

        # Eficiência teórica máxima (no regime crítico)
        if self.config.coupling_regime == CouplingRegime.CRITICAL:
            # No ponto crítico: g = (κ + γ)/4
            self.theoretical_efficiency = 4 * self.κ * self.γ / (self.κ + self.γ)**2
        else:
            # Eficiência geral: η = 4C / (1 + C)²
            self.theoretical_efficiency = 4 * self.cooperativity / (1 + self.cooperativity)**2

        # Ruído térmico ocupação (distribuição de Bose-Einstein)
        k_B = 1.38e-23  # J/K
        hbar = 1.05e-34  # J·s
        self.n_th_magnon = 1 / (np.exp(hbar * self.ω_m / (k_B * self.config.temperature_k)) - 1)
        self.n_th_photon = 1 / (np.exp(hbar * self.ω_c / (k_B * self.config.temperature_k)) - 1)

        print(f"   Derived: ω_m={self.ω_m/2/np.pi/1e9:.2f}GHz, γ/2π={self.γ/2/np.pi/1e6:.2f}MHz")
        print(f"   Cooperativity C = {self.cooperativity:.2f}, η_max = {self.theoretical_efficiency:.2%}")

    def transduce_magnon_to_photon(
        self,
        magnon_state: Union[float, torch.Tensor],  # Occupation ou estado quântico
        integration_time_us: float = 1.0,
        classical_readout: bool = True
    ) -> TransductionResult:
        """
        Transduz estado magnônico para sinal fotônico (leitura clássica).

        Args:
            magnon_state: Occupation ⟨a†a⟩ ou tensor de estado quântico
            integration_time_us: Tempo de integração para leitura
            classical_readout: Se retornar sinal clássico (intensidade) ou estado quântico

        Returns:
            TransductionResult com eficiência e ruído
        """
        start_time = time.time()

        # Extrair occupation magnônica
        if isinstance(magnon_state, torch.Tensor):
            # Estado quântico: calcular occupation esperado
            if magnon_state.dim() == 1:
                # Vetor de estado |ψ⟩
                n_magnon = torch.sum(torch.arange(len(magnon_state)) *
                                   torch.abs(magnon_state)**2).item()
            else:
                # Matriz densidade ρ
                n_magnon = torch.sum(torch.diag(magnon_state) *
                                   torch.arange(magnon_state.shape[0])).item()
        else:
            n_magnon = float(magnon_state)

        # Simular processo de transdução
        # Eficiência prática: η_practical = η_theoretical × fatores de perda
        impedance_factor = 1.0 if self.config.impedance_match else 0.7
        thermal_factor = np.exp(-self.n_th_magnon)  # Supressão térmica
        practical_efficiency = self.theoretical_efficiency * impedance_factor * thermal_factor

        # Energia de saída (em unidades de ℏω)
        output_energy = n_magnon * practical_efficiency

        # Ruído adicionado: ruído térmico + ruído quântico mínimo
        added_noise = self.n_th_photon + 0.5  # 0.5 é o ruído quântico mínimo (SQL)

        # Atualizar estado interno
        self.magnon_occupation = n_magnon * (1 - practical_efficiency)  # Magnons consumidos
        self.photon_occupation = output_energy

        # Coerência magnon-fóton (para regime forte)
        if self.config.coupling_regime in [CouplingRegime.STRONG, CouplingRegime.ULTRA_STRONG]:
            self.coherence = np.sqrt(n_magnon * output_energy) * np.exp(1j * np.random.uniform(0, 2*np.pi))

        # Atualizar métricas
        self.transduction_metrics['operations_count'] += 1
        self.transduction_metrics['avg_efficiency'] = (
            (self.transduction_metrics['avg_efficiency'] *
             (self.transduction_metrics['operations_count'] - 1) + practical_efficiency) /
            self.transduction_metrics['operations_count']
        )
        self.transduction_metrics['avg_added_noise'] = (
            (self.transduction_metrics['avg_added_noise'] *
             (self.transduction_metrics['operations_count'] - 1) + added_noise) /
            self.transduction_metrics['operations_count']
        )

        if output_energy > 0:
            self.transduction_metrics['successful_transductions'] += 1
        else:
            self.transduction_metrics['failed_transductions'] += 1

        result = TransductionResult(
            success=output_energy > 1e-10,
            input_type='magnon',
            output_type='photon',
            input_energy=n_magnon,
            output_energy=output_energy,
            efficiency=practical_efficiency,
            added_noise_photons=added_noise,
            timestamp=start_time,
            metadata={
                'integration_time_us': integration_time_us,
                'cooperativity': self.cooperativity,
                'thermal_occupation_magnon': self.n_th_magnon,
                'thermal_occupation_photon': self.n_th_photon,
                'classical_readout': classical_readout
            }
        )

        # Notificar callbacks
        for callback in self.transduction_callbacks:
            try:
                callback({
                    'type': 'transduction_completed',
                    'direction': 'magnon_to_photon',
                    'result': {
                        'efficiency': result.efficiency,
                        'snr': result.signal_to_noise_ratio(),
                        'added_noise': result.added_noise_photons
                    },
                    'timestamp': start_time
                })
            except Exception as e:
                print(f"⚠️ Transduction callback error: {e}")

        return result

    def transduce_photon_to_magnon(
        self,
        photon_input: Union[float, Dict[str, Any]],  # Intensidade ou especificação de pulso
        pulse_duration_us: float = 0.1,
        phase_reference: Optional[float] = None
    ) -> TransductionResult:
        """
        Transduz sinal fotônico para excitação magnônica (escrita clássica).

        Args:
            photon_input: Intensidade de fótons ou dict com especificação de pulso
            pulse_duration_us: Duração do pulso de escrita
            phase_reference: Fase de referência para coerência quântica

        Returns:
            TransductionResult com eficiência e ruído
        """
        start_time = time.time()

        # Extrair intensidade fotônica de entrada
        if isinstance(photon_input, dict):
            n_photon = photon_input.get('intensity', photon_input.get('photon_count', 1.0))
            input_phase = photon_input.get('phase', 0.0)
        else:
            n_photon = float(photon_input)
            input_phase = 0.0

        # Eficiência de escrita (geralmente menor que leitura devido a perdas de acoplamento)
        write_efficiency = self.theoretical_efficiency * 0.8  # Fator de perda adicional para escrita

        # Excitação magnônica gerada
        generated_magnons = n_photon * write_efficiency

        # Ruído adicionado: dominado por ruído térmico magnônico em baixas temperaturas
        added_noise = self.n_th_magnon + 0.1  # Ruído de escrita adicional

        # Se fase de referência fornecida e regime forte: preservar coerência
        if phase_reference is not None and self.config.coupling_regime in [
            CouplingRegime.STRONG, CouplingRegime.ULTRA_STRONG, CouplingRegime.CRITICAL
        ]:
            # Preservar fase relativa com referência
            self.coherence = np.sqrt(generated_magnons * n_photon) * np.exp(1j * phase_reference)

        # Atualizar estado interno
        self.photon_occupation = n_photon * (1 - write_efficiency)
        self.magnon_occupation = generated_magnons

        # Atualizar métricas
        self.transduction_metrics['operations_count'] += 1
        self.transduction_metrics['avg_efficiency'] = (
            (self.transduction_metrics['avg_efficiency'] *
             (self.transduction_metrics['operations_count'] - 1) + write_efficiency) /
            self.transduction_metrics['operations_count']
        )

        if generated_magnons > 0:
            self.transduction_metrics['successful_transductions'] += 1
        else:
            self.transduction_metrics['failed_transductions'] += 1

        result = TransductionResult(
            success=generated_magnons > 1e-10,
            input_type='photon',
            output_type='magnon',
            input_energy=n_photon,
            output_energy=generated_magnons,
            efficiency=write_efficiency,
            added_noise_photons=added_noise,
            timestamp=start_time,
            metadata={
                'pulse_duration_us': pulse_duration_us,
                'input_phase': input_phase,
                'phase_preserved': phase_reference is not None and self.coherence != 0,
                'cooperativity': self.cooperativity
            }
        )

        return result

    def bidirectional_transduce(
        self,
        input_signal: Union[float, torch.Tensor, Dict],
        direction: TransductionDirection,
        **kwargs
    ) -> TransductionResult:
        """
        Interface unificada para transdução bidirecional.
        """
        if direction == TransductionDirection.MAGNON_TO_PHOTON:
            return self.transduce_magnon_to_photon(input_signal, **kwargs)
        elif direction == TransductionDirection.PHOTON_TO_MAGNON:
            return self.transduce_photon_to_magnon(input_signal, **kwargs)
        else:
            # Auto-detectar baseado no tipo de entrada
            if isinstance(input_signal, (torch.Tensor, float)) or 'magnon' in str(type(input_signal)).lower():
                return self.transduce_magnon_to_photon(input_signal, **kwargs)
            else:
                return self.transduce_photon_to_magnon(input_signal, **kwargs)

    def calibrate(self, reference_source: str = 'internal') -> Dict[str, float]:
        """
        Calibra transdutor usando fonte de referência.

        Returns:
            Dict com parâmetros calibrados
        """
        print(f"🔧 Calibrating transducer {self.node_id} using {reference_source}...")

        # Medir ruído de fundo (sem sinal)
        background_photons = self.n_th_photon + np.random.normal(0, 0.01)

        # Medir resposta a sinal conhecido
        test_magnons = 100.0
        result = self.transduce_magnon_to_photon(test_magnons, integration_time_us=10.0)

        # Calcular eficiência medida
        measured_efficiency = result.output_energy / test_magnons if test_magnons > 0 else 0

        # Ajustar parâmetros se necessário
        efficiency_error = abs(measured_efficiency - self.theoretical_efficiency)
        if efficiency_error > 0.1:  # Mais de 10% de erro
            print(f"  ⚠️ Efficiency mismatch: measured={measured_efficiency:.2%}, expected={self.theoretical_efficiency:.2%}")
            # Em produção: ajustar parâmetros de acoplamento via feedback

        calibration_result = {
            'background_photons': background_photons,
            'measured_efficiency': measured_efficiency,
            'theoretical_efficiency': self.theoretical_efficiency,
            'efficiency_error': efficiency_error,
            'cooperativity_measured': (
                (1 - np.sqrt(1 - measured_efficiency)) /
                (1 + np.sqrt(1 - measured_efficiency))
                if measured_efficiency < 1 else self.cooperativity
            ),
            'calibration_timestamp': time.time()
        }

        print(f"  ✓ Calibration complete: η={measured_efficiency:.2%}, C={calibration_result['cooperativity_measured']:.2f}")
        return calibration_result

    def register_transduction_callback(self, callback: Callable[[Dict], None]):
        """Registra callback para eventos de transdução."""
        self.transduction_callbacks.append(callback)

    def get_transducer_status(self) -> Dict[str, Any]:
        """Retorna status detalhado do transdutor."""
        squeezed = self.compute_squeezing_parameter() if hasattr(self, 'compute_squeezing_parameter') else None

        return {
            'node_id': self.node_id,
            'config': {
                'magnon_frequency_ghz': self.config.magnon_frequency_ghz,
                'photon_frequency_ghz': self.config.photon_frequency_ghz,
                'coupling_regime': self.config.coupling_regime.name,
                'temperature_k': self.config.temperature_k
            },
            'derived_parameters': {
                'cooperativity': self.cooperativity,
                'theoretical_efficiency': self.theoretical_efficiency,
                'detuning_ghz': self.Δ / 2 / np.pi / 1e9,
                'thermal_occupation_magnon': self.n_th_magnon,
                'thermal_occupation_photon': self.n_th_photon
            },
            'current_state': {
                'magnon_occupation': self.magnon_occupation,
                'photon_occupation': self.photon_occupation,
                'coherence_magnitude': abs(self.coherence),
                'coherence_phase': np.angle(self.coherence) if self.coherence != 0 else None
            },
            'metrics': self.transduction_metrics,
            'squeezing': squeezed,
            'timestamp': time.time()
        }
