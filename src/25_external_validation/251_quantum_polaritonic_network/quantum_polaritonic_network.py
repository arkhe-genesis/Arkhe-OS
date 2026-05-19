# quantum_polaritonic_network.py — Substrato 251
# Simulação coletiva com matriz densidade e otimização de Φ_C global

import numpy as np
import hashlib, time
from scipy.linalg import expm
from dataclasses import dataclass
from typing import List, Tuple, Dict

@dataclass
class PhotonicNode:
    """Nó fotônico com graus de liberdade de polariton."""
    id: int
    gate_voltage: float = 0.0          # 0V = máximo acoplamento exciton-fóton
    exciton_energy_eV: float = 1.646    # Energia do exciton neutro (MoSe₂)
    cavity_energy_eV: float = 1.656     # Energia da cavidade nua
    rabi_splitting_meV: float = 35.0    # Ω — acoplamento exciton-fóton
    nonlinear_coefficient: float = 0.02 # Deslocamento não linear (meV·μm²)
    mode_volume_um3: float = 0.01       # Volume modal da nanocavidade

    def hamiltonian(self, exciton_density: float) -> np.ndarray:
        """Hamiltoniano efetivo 2x2 no subespaço LP-UP."""
        ex = self.exciton_energy_eV
        cav = self.cavity_energy_eV
        omega = self.rabi_splitting_meV / 1000  # eV

        blueshift = self.nonlinear_coefficient * exciton_density * self.mode_volume_um3 / 1000
        ex_shifted = ex + blueshift
        detuning = ex_shifted - cav

        H = np.array([[ex_shifted, omega/2],
                      [omega/2, cav]], dtype=complex)
        return H

class CollectivePhotonicNetwork:
    """Rede de N nós fotônicos com interação coletiva e otimização de Φ_C."""

    def __init__(self, n_nodes: int = 9):
        self.nodes = [PhotonicNode(i, gate_voltage=np.random.uniform(-2, 2)) for i in range(n_nodes)]
        self.n_nodes = n_nodes
        self.coupling_strength = 0.05  # meV de interação entre nós vizinhos

    def build_total_hamiltonian(self, exciton_densities: List[float]) -> np.ndarray:
        """Constrói Hamiltoniano total da rede no espaço de Fock truncado."""
        dim = 2 * self.n_nodes  # Cada nó: 2 modos (LP, UP)
        H_total = np.zeros((dim, dim), dtype=complex)

        for i, node in enumerate(self.nodes):
            H_node = node.hamiltonian(exciton_densities[i])
            H_total[2*i:2*i+2, 2*i:2*i+2] = H_node

        # Acoplamento entre nós vizinhos (hopping de polaritons)
        for i in range(self.n_nodes - 1):
            H_total[2*i, 2*(i+1)] = self.coupling_strength / 1000  # eV
            H_total[2*i+1, 2*(i+1)+1] = self.coupling_strength / 1000
            H_total[2*(i+1), 2*i] = np.conj(self.coupling_strength / 1000)
            H_total[2*(i+1)+1, 2*i+1] = np.conj(self.coupling_strength / 1000)

        return H_total

    def compute_global_phi_c(self, violation_vector: List[int]) -> float:
        """Φ_C global via evolução temporal e medida de coerência."""
        # Converte violações em densidades de excitons
        exciton_densities = [v * 1e12 for v in violation_vector]

        # Hamiltoniano total
        H = self.build_total_hamiltonian(exciton_densities)

        # Estado inicial: vácuo de polaritons
        psi_0 = np.zeros(2 * self.n_nodes, dtype=complex)
        psi_0[0] = 1.0  # Excita LP do primeiro nó

        # Evolução temporal (simplificada)
        t_evol = 1.0  # ps
        U = expm(-1j * H * t_evol / 0.658)  # 0.658 eV·ps = ℏ
        psi_t = U @ psi_0

        # Medida de coerência: pureza do estado reduzido de cada nó
        coherence_scores = []
        for i in range(self.n_nodes):
            rho_i = np.outer(psi_t[2*i:2*i+2], np.conj(psi_t[2*i:2*i+2]))
            purity = np.real(np.trace(rho_i @ rho_i))
            coherence_scores.append(min(1.0, purity))

        phi_c_global = np.mean(coherence_scores)
        return min(0.9999, phi_c_global)  # Sovereign Gap

    def optimize_gate_voltages(self, violation_vector: List[int]) -> Tuple[List[float], float]:
        """Otimiza tensões de porta para maximizar Φ_C global."""
        best_voltages = [0.0] * self.n_nodes
        best_phi_c = 0.0

        for _ in range(100):
            voltages = np.random.uniform(-2, 2, self.n_nodes)
            for i, node in enumerate(self.nodes):
                node.gate_voltage = voltages[i]
            phi_c = self.compute_global_phi_c(violation_vector)
            if phi_c > best_phi_c:
                best_phi_c = phi_c
                best_voltages = voltages.tolist()

        return best_voltages, best_phi_c
