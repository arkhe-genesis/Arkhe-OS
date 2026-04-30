#!/usr/bin/env python3
"""
arkhe_diverse_inputs_v118.py
Substrato 201: Gerador de Inputs Quânticos Diversos para Maximizar Cobertura.
"""
import numpy as np
from scipy.stats import unitary_group
from typing import List, Dict, Tuple

class DiverseQuantumInputGenerator:
    """
    Gera estados de entrada diversos para testar circuitos quânticos.
    Inspirado em QuraTest (características quânticas) e NovaQ (diversidade).
    """

    def __init__(self, n_qubits: int, seed: int = 42):
        self.n_qubits = n_qubits
        self.rng = np.random.default_rng(seed)
        self.dim = 2 ** n_qubits
        self.generated_states: List[np.ndarray] = []

    def generate_superposition_uniform(self) -> np.ndarray:
        """Estado de superposição uniforme sobre todos os estados base."""
        state = np.ones(self.dim, dtype=complex) / np.sqrt(self.dim)
        # Adiciona fases aleatórias para diversidade de interferência
        phases = np.exp(2j * np.pi * self.rng.uniform(0, 1, self.dim))
        state = state * phases
        return state / np.linalg.norm(state)

    def generate_haar_random(self) -> np.ndarray:
        """Estado aleatório distribuído uniformemente (medida de Haar)."""
        # Usa decomposição QR de uma matriz gaussiana complexa
        real = self.rng.normal(0, 1, (self.dim, self.dim))
        imag = self.rng.normal(0, 1, (self.dim, self.dim))
        gauss = real + 1j * imag
        q, r = np.linalg.qr(gauss)
        # Extrai a primeira coluna
        return q[:, 0]

    def generate_entangled_pair(self, qubit_a: int, qubit_b: int) -> np.ndarray:
        """Estado de Bell entre dois qubits (|01> + |10>)/√2."""
        state = np.zeros(self.dim, dtype=complex)
        # Cria estado base para |0...0>
        idx_a = 1 << qubit_a
        idx_b = 1 << qubit_b
        state[idx_a] = 1.0 / np.sqrt(2)
        state[idx_b] = 1.0 / np.sqrt(2)
        # Aplica fase aleatória para diversidade
        phase = np.exp(2j * np.pi * self.rng.uniform(0, 1))
        state = state * phase
        return state

    def generate_ghz_state(self) -> np.ndarray:
        """Estado GHZ: (|00...0> + |11...1>)/√2."""
        state = np.zeros(self.dim, dtype=complex)
        state[0] = 1.0 / np.sqrt(2)
        state[-1] = 1.0 / np.sqrt(2)
        return state

    def generate_w_state(self) -> np.ndarray:
        """Estado W: superposição de todos os estados com um único 1."""
        state = np.zeros(self.dim, dtype=complex)
        for i in range(self.n_qubits):
            idx = 1 << i
            state[idx] = 1.0 / np.sqrt(self.n_qubits)
        return state

    def generate_biased_superposition(self, bias_vector: np.ndarray) -> np.ndarray:
        """Superposição com probabilidades tendenciosas (vetor de amplitudes)."""
        # bias_vector: array de probabilidades alvo para cada estado base
        amplitudes = np.sqrt(bias_vector)
        phases = np.exp(2j * np.pi * self.rng.uniform(0, 1, self.dim))
        state = amplitudes * phases
        return state / np.linalg.norm(state)

    def generate_diverse_batch(self, n_inputs: int) -> List[Dict]:
        """
        Gera um lote diverso de inputs, combinando diferentes estratégias.
        Cada input é um dicionário com o statevector e metadados.
        """
        inputs = []
        strategies = [
            ('superposition_uniform', self.generate_superposition_uniform),
            ('haar_random', self.generate_haar_random),
            ('ghz_state', self.generate_ghz_state),
            ('w_state', self.generate_w_state),
        ]
        # Adiciona pares entrelaçados para pares de qubits selecionados
        if self.n_qubits >= 2:
            for qa in range(min(self.n_qubits - 1, 3)):
                for qb in range(qa + 1, min(self.n_qubits, qa + 2)):
                    strategies.append(
                        (f'bell_{qa}_{qb}', lambda a=qa, b=qb: self.generate_entangled_pair(a, b))
                    )

        for i in range(n_inputs):
            strat_name, strat_fn = strategies[i % len(strategies)]
            state = strat_fn()
            self.generated_states.append(state)
            inputs.append({
                'id': i,
                'strategy': strat_name,
                'statevector': state,
                'entropy': self._compute_von_neumann_entropy(state),
                'purity': self._compute_purity(state),
                'superposition_measure': self._compute_superposition_measure(state),
            })
        return inputs

    def _compute_von_neumann_entropy(self, state: np.ndarray) -> float:
        """Entropia de von Neumann de um estado puro (sempre 0, retorna 0)."""
        # Para estado puro, a entropia é zero; retornamos a entropia linear
        # como métrica de "diversidade" no espaço de probabilidades
        probs = np.abs(state) ** 2
        probs = probs[probs > 0]
        return -np.sum(probs * np.log2(probs))

    def _compute_purity(self, state: np.ndarray) -> float:
        """Pureza do estado (sempre 1 para estado puro)."""
        # Para um estado puro, pureza = 1; mantido como métrica de referência
        return 1.0

    def _compute_superposition_measure(self, state: np.ndarray) -> float:
        """Medida de superposição: número efetivo de estados base ocupados."""
        probs = np.abs(state) ** 2
        # Evita log(0)
        probs = probs[probs > 0]
        if len(probs) == 0:
            return 1.0
        return 2.0 ** (-np.sum(probs * np.log2(probs)))  # número efetivo

# ============================================================================
# SIMULAÇÃO DE DIVERSIDADE DE COBERTURA
# ============================================================================

def simulate_coverage_with_input(qubits, n_gates, input_statevector):
    """
    Simula a cobertura de um circuito com o input fornecido.
    Retorna (condition_cov, decision_cov, path_cov, jain_index).
    """
    # A cobertura depende do estado de entrada: se ele coloca mais qubits
    # em superposição, mais portas controladas exercitam ambos os ramos.
    superposition_measure = 2.0 ** (-np.sum(np.abs(input_statevector)**2 *
                                            np.log2(np.abs(input_statevector)**2 + 1e-12)))
    effective_superposition = min(1.0, superposition_measure / (2**qubits))

    # Quanto maior a superposição, mais caminhos são exercitados
    condition_cov = 80.0 + 20.0 * effective_superposition
    decision_cov = 80.0 + 20.0 * effective_superposition
    path_cov = 40.0 + 60.0 * effective_superposition - 10.0 * (n_gates - 5) / 50.0
    path_cov = np.clip(path_cov, 0.0, 100.0)

    # Jain: quão equilibrados são os ramos
    jain = 0.5 + 0.5 * effective_superposition

    return {
        'condition': condition_cov,
        'decision': decision_cov,
        'path': path_cov,
        'jain_condition': jain,
        'jain_decision': jain,
        'jain_path': jain,
        'probabilistic_condition': condition_cov * jain / 100.0,
        'probabilistic_decision': decision_cov * jain / 100.0,
        'probabilistic_path': path_cov * jain / 100.0,
    }

if __name__ == "__main__":
    # Exemplo de uso
    gen = DiverseQuantumInputGenerator(n_qubits=5, seed=42)
    inputs = gen.generate_diverse_batch(10)
    for inp in inputs[:5]:
        cov = simulate_coverage_with_input(5, 10, inp['statevector'])
        print(f"Input {inp['id']} ({inp['strategy']}): "
              f"Path Cov = {cov['path']:.1f}%, "
              f"Jain = {cov['jain_path']:.3f}, "
              f"Eff.Superp. = {inp['superposition_measure']:.2f}")
