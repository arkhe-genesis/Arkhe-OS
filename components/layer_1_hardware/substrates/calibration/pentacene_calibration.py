"""
Calibração do simulador tight-binding de pentaceno com dados experimentais.
Objetivo: ajustar parâmetros {t0, alpha_gate, onsite_energy} para minimizar
erro entre latências simuladas e medidas em hardware real.
"""

import torch
import numpy as np
from typing import Dict, List, Optional, Tuple
from scipy.optimize import least_squares
from dataclasses import dataclass
import time

@dataclass
class CalibrationData:
    """Dados experimentais para calibração."""
    gate_voltage: torch.Tensor  # [N_sites]
    measured_latency_ms: float  # latência medida para operação específica
    measured_current_uA: float  # corrente de dreno medida
    temperature_K: float
    timestamp: float

class PentaceneCalibrator:
    """
    Calibrador do modelo tight-binding via otimização de parâmetros.
    Minimiza: L = w₁·(lat_sim - lat_exp)² + w₂·(I_sim - I_exp)² + w₃·‖θ‖²
    """

    def __init__(
        self,
        simulator_class,  # PentaceneTightBindingSimulator
        initial_params: Dict[str, float],
        param_bounds: Dict[str, Tuple[float, float]],
        loss_weights: Dict[str, float] = None
    ):
        self.simulator_class = simulator_class
        self.params = initial_params.copy()
        self.bounds = param_bounds
        self.weights = loss_weights or {'latency': 1.0, 'current': 0.5, 'regularization': 0.01}

        # Histórico de calibração
        self.calibration_history: List[Dict] = []

    def simulate_with_params(
        self,
        params: Dict[str, float],
        config: 'PentaceneConfig',
        gate_voltage: torch.Tensor,
        operation: str = 'hamiltonian_compute'
    ) -> Dict[str, float]:
        """Executa simulação com parâmetros dados e retorna métricas."""
        # Atualizar config com parâmetros
        config.t0 = params['t0']
        config.alpha_gate = params['alpha_gate']
        config.onsite_energy = params['onsite_energy']

        # Instanciar simulador
        sim = self.simulator_class(config)
        sim.apply_gate_voltage(gate_voltage)

        # Medir latência e corrente
        latency = sim.measure_latency(operation)
        current = sim.compute_drain_current(
            source_idx=0,
            drain_idx=sim.total_sites - 1,
            bias_voltage=0.1
        )

        return {'latency_ms': latency, 'current_uA': current * 1e6}

    def loss_function(
        self,
        param_vector: np.ndarray,
        calibration_data: CalibrationData,
        config: 'PentaceneConfig'
    ) -> np.ndarray:
        """
        Função de perda para otimização: diferenças normalizadas entre simulação e experimento.
        param_vector: [t0, alpha_gate, onsite_energy]
        """
        # Reconstruir dicionário de parâmetros
        param_names = ['t0', 'alpha_gate', 'onsite_energy']
        params = {name: val for name, val in zip(param_names, param_vector)}

        # Simular com parâmetros atuais
        sim_result = self.simulate_with_params(
            params, config, calibration_data.gate_voltage
        )

        # Calcular resíduos normalizados
        residuals = []

        # Resíduo de latência
        lat_diff = (sim_result['latency_ms'] - calibration_data.measured_latency_ms)
        residuals.append(self.weights['latency'] * lat_diff / calibration_data.measured_latency_ms)

        # Resíduo de corrente
        curr_diff = (sim_result['current_uA'] - calibration_data.measured_current_uA)
        residuals.append(self.weights['current'] * curr_diff / max(1e-6, calibration_data.measured_current_uA))

        # Regularização L2 dos parâmetros (evitar overfitting)
        for name, val in params.items():
            residuals.append(np.sqrt(self.weights['regularization']) * (val - self.params[name]))

        return np.array(residuals)

    def calibrate(
        self,
        calibration_data: List[CalibrationData],
        config_template: 'PentaceneConfig',
        max_iterations: int = 100
    ) -> Dict[str, any]:
        """
        Executa calibração via least_squares (Levenberg-Marquardt).
        """
        param_names = ['t0', 'alpha_gate', 'onsite_energy']
        initial_vector = np.array([self.params[name] for name in param_names])
        bounds_vector = ([self.bounds[name][0] for name in param_names],
                        [self.bounds[name][1] for name in param_names])

        # Função objetivo agregada sobre todos os dados de calibração
        def aggregated_loss(param_vec):
            total_residuals = []
            for data in calibration_data:
                residuals = self.loss_function(param_vec, data, config_template)
                total_residuals.extend(residuals)
            return np.array(total_residuals)

        # Otimização
        result = least_squares(
            aggregated_loss,
            initial_vector,
            bounds=bounds_vector,
            max_nfev=max_iterations,
            method='trf'  # Trust Region Reflective
        )

        # Atualizar parâmetros otimizados
        optimized_params = {name: val for name, val in zip(param_names, result.x)}
        self.params.update(optimized_params)

        # Registrar histórico
        self.calibration_history.append({
            'timestamp': time.time(),
            'optimized_params': optimized_params,
            'cost': result.cost,
            'success': result.success,
            'nfev': result.nfev
        })

        return {
            'optimized_params': optimized_params,
            'initial_params': self.params,
            'final_cost': result.cost,
            'converged': result.success,
            'iterations': result.nfev
        }

async def run_hardware_calibration():
    """Executa calibração com dados reais do hardware (mock)."""
    # Usando os types simulados para evitar erro
    from layer_1_hardware.substrates.v144.qdi_pentacene_tightbinding import QuantumDigitalInterfacePentacene, PentaceneConfig, PentaceneTightBindingSimulator

    # 1. Conectar ao hardware via QDI
    qdi = QuantumDigitalInterfacePentacene(
        simulator=PentaceneTightBindingSimulator(PentaceneConfig(Nx=20, Ny=20)),  # usar hardware real em prod
        max_latency_ms=100.0,
        min_fidelity=0.95
    )

    # 2. Gerar configurações de gate para teste
    test_configs = []
    for Vg_level in np.linspace(0, 5, 10):
        gate_matrix = torch.ones(20, 20) * Vg_level
        test_configs.append(gate_matrix)

    # 3. Coletar dados experimentais
    calibration_data = []
    for gate_voltage in test_configs:
        # Handshake e medição
        handshake = await qdi.handshake(gate_voltage.view(-1))
        if handshake['success']:
            write_result = qdi.write_quantum_state(gate_voltage.view(-1))

            calibration_data.append(CalibrationData(
                gate_voltage=gate_voltage.view(-1),
                measured_latency_ms=write_result['latency_ms'],
                measured_current_uA=write_result.get('drain_current_uA', 0.1), # default
                temperature_K=300.0,  # assumir temperatura controlada
                timestamp=time.time()
            ))

    # 4. Executar calibração
    config_template = PentaceneConfig(Nx=20, Ny=20)
    calibrator = PentaceneCalibrator(
        simulator_class=PentaceneTightBindingSimulator,
        initial_params={'t0': 0.1, 'alpha_gate': 0.15, 'onsite_energy': 0.0},
        param_bounds={
            't0': (0.01, 0.5),
            'alpha_gate': (0.05, 0.3),
            'onsite_energy': (-1.0, 1.0)
        }
    )

    result = calibrator.calibrate(calibration_data, config_template)

    print(f"✅ Calibração concluída: custo={result['final_cost']:.4f}, convergido={result['converged']}")
    print(f"   Parâmetros otimizados: {result['optimized_params']}")

    return result
