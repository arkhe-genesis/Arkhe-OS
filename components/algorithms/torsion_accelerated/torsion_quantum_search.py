# algorithms/torsion_accelerated/torsion_quantum_search.py
# Algoritmo de busca quântica acelerado via acoplamento de torção

import numpy as np
from typing import Callable, Optional, Tuple, Dict
from dataclasses import dataclass
import time

@dataclass
class TorsionSearchConfig:
    """Configuração para busca quântica com torção."""
    n_items: int  # tamanho do espaço de busca
    torsion_strength: float = 2.04
    torsion_coupling: float = 0.1  # parâmetro α no operador A_T
    max_iterations: int = 100
    convergence_threshold: float = 1e-6

class TorsionQuantumSearch:
    """
    Algoritmo de busca quântica acelerado por torção.

    Base: Grover search com Hamiltoniano modificado:
    H_T = H_Grover + α T_{μνρ} Γ^{μνρ}

    A torção induz mistura de componentes que acelera convergência.
    """

    def __init__(self, config: TorsionSearchConfig):
        self.config = config
        self.N = config.n_items
        self.n_qubits = int(np.ceil(np.log2(self.N)))

        # Construir operadores
        self.oracle = None  # definido pelo usuário
        self.diffusion = self._build_diffusion_operator()
        self.torsion_operator = self._build_torsion_operator()

    def _build_diffusion_operator(self) -> np.ndarray:
        """Constrói operador de difusão de Grover: 2|s⟩⟨s| - I."""
        # Estado uniforme |s⟩ = H^{⊗n}|0⟩
        H = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
        import functools
        H_n = functools.reduce(np.kron, [H] * self.n_qubits)
        s = H_n @ np.array([1] + [0]*(2**self.n_qubits - 1))

        # Operador de difusão
        D = 2 * np.outer(s, s.conj()) - np.eye(2**self.n_qubits)
        return D

    def _build_torsion_operator(self) -> np.ndarray:
        """
        Constrói operador de torção A_T = exp(i α T_{μνρ} Γ^{μνρ}).

        Simplificação para espaço de busca:
        Γ^{μνρ} ≈ σ^3 ⊗ σ^3 ⊗ ... (produto de Pauli-Z)
        """
        T = self.config.torsion_strength
        alpha = self.config.torsion_coupling

        # Operador de torção simplificado: produto de Z em pares de qubits
        Z = np.array([[1, 0], [0, -1]])
        torsion_gen = np.eye(2**self.n_qubits, dtype=complex)

        # Aplicar termo de torção em pares de qubits
        for i in range(0, self.n_qubits - 1, 2):
            # Construir Z⊗Z no par (i, i+1)
            ops = []
            for q in range(self.n_qubits):
                if q == i or q == i + 1:
                    ops.append(Z)
                else:
                    ops.append(np.eye(2))

            import functools
            Z_pair = functools.reduce(np.kron, ops)
            torsion_gen = torsion_gen @ Z_pair

        # Exponencial: exp(i α T torsion_gen)
        # Como torsion_gen² = I, temos exp(iθ G) = cos(θ)I + i sin(θ)G
        theta = alpha * T
        return np.cos(theta) * np.eye(2**self.n_qubits) + 1j * np.sin(theta) * torsion_gen

    def set_oracle(self, marked_item: int):
        """Configura oráculo para item marcado."""
        def oracle(state: np.ndarray) -> np.ndarray:
            # Oracle de Grover: inverte fase do estado marcado
            result = state.copy()
            result[marked_item] *= -1
            return result
        self.oracle = oracle

    def iterate_with_torsion(self, state: np.ndarray) -> np.ndarray:
        """
        Executa uma iteração do algoritmo com aceleração de torção.

        Sequência: oracle → torsion → diffusion
        """
        if self.oracle is None:
            raise ValueError("Oracle not set. Call set_oracle() first.")

        # Aplicar oráculo
        state = self.oracle(state)

        # Aplicar operador de torção
        state = self.torsion_operator @ state

        # Aplicar difusão
        state = self.diffusion @ state

        return state

    def search(self, marked_item: int, initial_state: Optional[np.ndarray] = None) -> Dict:
        """
        Executa busca quântica acelerada por torção.

        Returns:
            Dict com item encontrado, iterações, e métricas de convergência
        """
        self.set_oracle(marked_item)

        # Estado inicial: superposição uniforme
        if initial_state is None:
            H = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
            import functools
            H_n = functools.reduce(np.kron, [H] * self.n_qubits)
            state = H_n @ np.array([1] + [0]*(2**self.n_qubits - 1))
        else:
            state = initial_state.copy()

        # Iterar até convergência ou max_iterations
        start_time = time.time()
        amplitudes = []

        iteration = 0
        for iteration in range(self.config.max_iterations):
            state = self.iterate_with_torsion(state)

            # Monitorar amplitude do item marcado
            amp_marked = np.abs(state[marked_item])**2
            amplitudes.append(amp_marked)

            # Verificar convergência
            if amp_marked > 1 - self.config.convergence_threshold:
                break

        # Encontrar item mais provável
        found_item = int(np.argmax(np.abs(state)**2))
        success = (found_item == marked_item)

        return {
            'found_item': found_item,
            'success': success,
            'iterations': iteration + 1,
            'final_amplitude': np.abs(state[marked_item])**2,
            'amplitude_history': amplitudes,
            'execution_time_ms': (time.time() - start_time) * 1000,
            'theoretical_grover_iterations': int(np.pi/4 * np.sqrt(self.N)),
            'speedup_factor': (np.pi/4 * np.sqrt(self.N)) / (iteration + 1) if iteration > 0 else 1.0
        }

    def compare_with_standard_grover(self, marked_item: int) -> Dict:
        """
        Compara desempenho com Grover padrão (sem torção).
        """
        # Executar busca com torção
        torsion_result = self.search(marked_item)

        # Executar Grover padrão (desativar torção)
        original_torsion = self.torsion_operator
        self.torsion_operator = np.eye(2**self.n_qubits)  # identidade = sem torção
        standard_result = self.search(marked_item)
        self.torsion_operator = original_torsion

        return {
            'torsion': torsion_result,
            'standard': standard_result,
            'speedup': standard_result['iterations'] / torsion_result['iterations'] if torsion_result['iterations'] > 0 else 1.0
        }
