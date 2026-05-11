#!/usr/bin/env python3
"""
qiskit_integration.py — Interface ARKHE ↔ Qiskit/Pennylane para execução em hardware quântico.
Mapeia políticas de mitigação de bursts para circuitos de eco de spin e medições de coerência.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
import time

# Optional imports for quantum backends
try:
    from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
    from qiskit.providers import Backend, Job
    from qiskit_aer import AerSimulator
    from qiskit.primitives import Sampler, Estimator
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False

try:
    import pennylane as qml
    from pennylane import numpy as pnp
    PENNYLANE_AVAILABLE = True
except ImportError:
    PENNYLANE_AVAILABLE = False

@dataclass
class QuantumCircuitConfig:
    """Configuração para circuito quântico de mitigação."""
    num_qubits: int = 1
    echo_pulses: bool = True
    dynamical_decoupling: str = 'XY4'  # 'XY4', 'CPMG', 'UDD'
    measurement_basis: str = 'Z'  # 'X', 'Y', 'Z'
    shots: int = 1024
    backend_name: str = 'aer_simulator'

class QiskitQuantumInterface:
    """
    Interface ARKHE ↔ Qiskit para execução de circuitos de mitigação quântica.
    """

    def __init__(self, config: Optional[QuantumCircuitConfig] = None):
        if not QISKIT_AVAILABLE:
            raise ImportError("Qiskit not installed. Install with: pip install qiskit qiskit-aer")

        self.config = config or QuantumCircuitConfig()
        self.backend = AerSimulator() if self.config.backend_name == 'aer_simulator' else None
        self.sampler = Sampler(backend=self.backend) if self.backend else None

    def build_echo_circuit(
        self,
        qubit_index: int = 0,
        echo_time_ns: float = 750.0,
        initial_state: Optional[str] = None
    ) -> 'QuantumCircuit':
        """
        Constrói circuito de eco de spin para mitigação de dephasing.

        Args:
            qubit_index: índice do qubit alvo
            echo_time_ns: tempo de evolução livre antes/depois do pulso π
            initial_state: estado inicial ('|0⟩', '|1⟩', '|+⟩', '|-⟩')

        Returns:
            QuantumCircuit configurado para medição de coerência
        """
        qr = QuantumRegister(self.config.num_qubits, 'q')
        cr = ClassicalRegister(self.config.num_qubits, 'c')
        qc = QuantumCircuit(qr, cr)

        # Preparar estado inicial
        if initial_state == '|+⟩':
            qc.h(qubit_index)
        elif initial_state == '|-⟩':
            qc.x(qubit_index)
            qc.h(qubit_index)
        elif initial_state == '|1⟩':
            qc.x(qubit_index)
        # else: |0⟩ por padrão

        # Evolução livre simulada (em hardware real: wait/IDLE)
        # Em simulação: aplicar fase aleatória proporcional ao gap
        if self.config.echo_pulses:
            # Primeiro período de evolução
            qc.rz(np.random.normal(0, 0.1), qubit_index)  # ruído de fase simulado

            # Pulso π de eco (R_x(π))
            qc.rx(np.pi, qubit_index)

            # Segundo período de evolução
            qc.rz(np.random.normal(0, 0.1), qubit_index)

        # Sequência de desacoplamento dinâmico (opcional)
        if self.config.dynamical_decoupling == 'XY4':
            for _ in range(2):
                qc.rx(np.pi, qubit_index)
                qc.ry(np.pi, qubit_index)
                qc.rx(np.pi, qubit_index)
                qc.ry(np.pi, qubit_index)

        # Medição na base especificada
        if self.config.measurement_basis == 'X':
            qc.h(qubit_index)
        elif self.config.measurement_basis == 'Y':
            qc.sdg(qubit_index)
            qc.h(qubit_index)

        qc.measure(qubit_index, qubit_index)

        return qc

    def execute_circuit(
        self,
        circuit: 'QuantumCircuit',
        gap_estimate: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Executa circuito e retorna estatísticas de coerência.

        Args:
            circuit: circuito quântico a executar
            gap_estimate: estimativa do gap Kolmogorov para injeção de ruído realista

        Returns:
            Dict com probabilidades de medição, fidelidade estimada, etc.
        """
        if self.sampler is None:
            raise RuntimeError("Sampler not initialized")

        # Injetar ruído baseado no gap estimado (simulação realista)
        if gap_estimate is not None:
            # Gap alto → mais ruído de fase
            phase_noise_std = 0.05 + gap_estimate * 0.02
            # Aplicar ruído adicional ao circuito (em hardware real: calibrar pulsos)

        # Executar via Sampler primitive
        job = self.sampler.run([circuit], shots=self.config.shots)
        result = job.result()

        # Extrair quasiprobabilidades
        quasi_probs = result.quasi_dists[0]

        # Calcular métricas de coerência
        prob_0 = sum(p for b, p in quasi_probs.items() if (b & 1) == 0)
        prob_1 = sum(p for b, p in quasi_probs.items() if (b & 1) == 1)

        # Fidelidade estimada (comparar com estado ideal)
        # Simplificação: fidelidade = |⟨ψ_ideal|ψ_measured⟩|²
        fidelity = max(prob_0, prob_1) if self.config.measurement_basis == 'Z' else 0.5

        return {
            'prob_0': prob_0,
            'prob_1': prob_1,
            'fidelity_estimate': fidelity,
            'coherence_measure': abs(prob_0 - prob_1),  # proxy para |⟨σ_z⟩|
            'shots': self.config.shots,
            'timestamp': time.time()
        }

    def batch_execute(
        self,
        circuits: List['QuantumCircuit'],
        gap_estimates: Optional[List[float]] = None
    ) -> List[Dict[str, float]]:
        """Executa múltiplos circuitos em batch (para paralelismo quântico)."""
        if gap_estimates is None:
            gap_estimates = [None] * len(circuits)

        results = []
        for circuit, gap in zip(circuits, gap_estimates):
            result = self.execute_circuit(circuit, gap)
            results.append(result)

        return results


class PennylaneQuantumInterface:
    """
    Interface ARKHE ↔ Pennylane para otimização de circuitos variacionais.
    Útil para treinar políticas de mitigação via gradientes quânticos.
    """

    def __init__(self, device_name: str = 'default.qubit', wires: int = 4):
        if not PENNYLANE_AVAILABLE:
            raise ImportError("PennyLane not installed. Install with: pip install pennylane")

        self.device = qml.device(device_name, wires=wires)
        self.wires = wires

        # dynamic qnode wrapping in init because qml might not be defined at module level
        # if PENNYLANE_AVAILABLE is False
        self.variational_echo_circuit = qml.qnode(self.device)(self._variational_echo_circuit_impl)

    def _variational_echo_circuit_impl(
        self,
        params: np.ndarray,
        gap_input: float,
        wire: int = 0
    ) -> float:
        """
        Circuito variacional para otimização de mitigação de bursts.

        Args:
            params: parâmetros treináveis do circuito [θ₁, θ₂, ..., θₙ]
            gap_input: estimativa do gap Kolmogorov (entrada clássica)
            wire: qubit alvo

        Returns:
            Valor esperado de ⟨σ_z⟩ como medida de coerência residual
        """
        # Codificar gap como ângulo de rotação
        qml.RY(gap_input * 0.1, wires=wire)

        # Camadas variacionais (ansatz)
        for i, theta in enumerate(params):
            qml.RX(theta, wires=wire)
            qml.RZ(params[(i + len(params)//2) % len(params)], wires=wire)

        # Medição
        return qml.expval(qml.PauliZ(wire))

    def compute_gradient(
        self,
        params: np.ndarray,
        gap_input: float,
        wire: int = 0
    ) -> np.ndarray:
        """Computa gradiente do circuito variacional via parameter-shift."""
        # Parameter-shift rule para gradientes quânticos
        shift = np.pi / 2
        grad = np.zeros_like(params)

        for i in range(len(params)):
            params_plus = params.copy()
            params_minus = params.copy()
            params_plus[i] += shift
            params_minus[i] -= shift

            exp_plus = self.variational_echo_circuit(params_plus, gap_input, wire)
            exp_minus = self.variational_echo_circuit(params_minus, gap_input, wire)

            grad[i] = 0.5 * (exp_plus - exp_minus)

        return grad
