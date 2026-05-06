# substrates/v174_hodge_duality/quantum_hilbert_duality.py
# Dualidade de Hodge explícita para espaços de Hilbert de qubits

import numpy as np
import torch
from typing import Dict, List, Optional, Union
from dataclasses import dataclass

@dataclass
class QuantumSystemConfig:
    """Configuração de sistema quântico para dualidade."""
    n_qubits: int
    hilbert_space_dim: int = None  # calculado como 2^n_qubits
    charge_conjugation_type: str = 'standard'  # 'standard', 'particle_hole', 'time_reversal'

    def __post_init__(self):
        if self.hilbert_space_dim is None:
            self.hilbert_space_dim = 2 ** self.n_qubits

class QuantumHodgeDuality:
    """
    Implementa a dualidade de Hodge quântica ★_ℋ: B(ℋ) → B(ℋ).

    ★_ℋ(O) = J O† J^{-1}, onde J é operador anti-unitário de conjugação.
    """

    def __init__(self, config: QuantumSystemConfig):
        self.config = config
        self.dim = config.hilbert_space_dim

        # Construir operador de conjugação de carga J
        self.J = self._build_charge_conjugation_operator()

        # Cache para operadores duais comuns
        self.dual_cache: Dict[str, np.ndarray] = {}

    def _build_charge_conjugation_operator(self) -> np.ndarray:
        """Constrói operador anti-unitário J para conjugação de carga."""
        if self.config.n_qubits == 1:
            # Para 1 qubit: J = iσ^2 ∘ K
            sigma_2 = np.array([[0, -1j], [1j, 0]])
            return 1j * sigma_2

        elif self.config.n_qubits > 1:
            # Para N qubits: J = ⊗^N (iσ^2) ∘ K
            sigma_2 = np.array([[0, -1j], [1j, 0]])
            J_unitary = 1j * sigma_2
            for _ in range(1, self.config.n_qubits):
                J_unitary = np.kron(J_unitary, 1j * sigma_2)
            return J_unitary

        else:
            # Fallback: conjugação complexa pura
            return np.eye(self.dim)

    def hodge_dual_operator(self, operator: np.ndarray, cache_key: Optional[str] = None) -> np.ndarray:
        """
        Calcula o dual de Hodge de um operador: ★_ℋ(O) = J O† J^{-1}.

        Args:
            operator: matriz do operador em ℋ
            cache_key: chave opcional para cache

        Returns:
            Matriz do operador dual
        """
        if cache_key and cache_key in self.dual_cache:
            return self.dual_cache[cache_key]

        # Calcular ★_ℋ(O) = J O† J† (pois J^{-1} = J† para unitário)
        O_dag = operator.T.conj()
        dual = self.J @ O_dag @ self.J.T.conj()

        if cache_key:
            self.dual_cache[cache_key] = dual

        return dual

    def is_self_dual(self, operator: np.ndarray, tolerance: float = 1e-10) -> bool:
        """Verifica se operador é auto-dual: ★_ℋ(O) = O."""
        dual = self.hodge_dual_operator(operator)
        return np.allclose(operator, dual, atol=tolerance)

    def decompose_into_dual_parts(self, operator: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Decompõe operador em partes auto-dual e anti-auto-dual:
        O = O_+ + O_-, onde O_± = ½(O ± ★_ℋ(O))
        """
        dual = self.hodge_dual_operator(operator)
        O_plus = 0.5 * (operator + dual)   # parte auto-dual
        O_minus = 0.5 * (operator - dual)  # parte anti-auto-dual

        return {
            'self_dual_part': O_plus,
            'anti_self_dual_part': O_minus,
            'self_dual_weight': np.linalg.norm(O_plus, 'fro')**2 / np.linalg.norm(operator, 'fro')**2,
            'anti_self_dual_weight': np.linalg.norm(O_minus, 'fro')**2 / np.linalg.norm(operator, 'fro')**2
        }

    def dual_state(self, density_matrix: np.ndarray) -> np.ndarray:
        """Calcula estado dual: ρ_★ = ★_ℋ(ρ)."""
        return self.hodge_dual_operator(density_matrix, cache_key=f"state_{id(density_matrix)}")

    def verify_trace_invariance(self, rho: np.ndarray, O: np.ndarray) -> Dict:
        """
        Verifica invariância do valor esperado sob dualidade:
        Tr[ρ O] = Tr[★ρ ★O]
        """
        # Valor esperado original
        exp_original = np.trace(rho @ O)

        # Valor esperado dual
        rho_dual = self.dual_state(rho)
        O_dual = self.hodge_dual_operator(O)
        exp_dual = np.trace(rho_dual @ O_dual)

        # Diferença
        diff = np.abs(exp_original - exp_dual)
        rel_diff = diff / (np.abs(exp_original) + 1e-12)

        return {
            'original_expectation': exp_original,
            'dual_expectation': exp_dual,
            'absolute_difference': diff,
            'relative_difference': rel_diff,
            'invariant': rel_diff < 1e-10
        }

    def bell_state_duality(self) -> Dict:
        """
        Analisa dualidade para estados de Bell.

        Estados de Bell são auto-duais sob ★_ℋ para conjugação padrão.
        """
        # Estado de Bell |Φ⁺⟩ = (|00⟩ + |11⟩)/√2
        bell_phi_plus = np.zeros((self.dim, self.dim), dtype=complex)
        if self.config.n_qubits >= 2:
            bell_phi_plus[0, 0] = 1/np.sqrt(2)
            bell_phi_plus[3, 3] = 1/np.sqrt(2)  # |11⟩⟨11|
            # Termos cruzados |00⟩⟨11| + |11⟩⟨00|
            bell_phi_plus[0, 3] = 1/np.sqrt(2)
            bell_phi_plus[3, 0] = 1/np.sqrt(2)

        # Verificar auto-dualidade
        is_sd = self.is_self_dual(bell_phi_plus)
        decomp = self.decompose_into_dual_parts(bell_phi_plus)

        return {
            'state_name': 'Bell_Phi_Plus',
            'is_self_dual': is_sd,
            'decomposition': decomp,
            'purity': np.trace(bell_phi_plus @ bell_phi_plus).real
        }

    def quantum_channel_duality(self, kraus_operators: List[np.ndarray]) -> List[np.ndarray]:
        """
        Calcula canal quântico dual: se ℰ(ρ) = Σ K_i ρ K_i†,
        então ℰ_★(ρ) = Σ ★(K_i) ρ ★(K_i)†
        """
        dual_kraus = []
        for i, K in enumerate(kraus_operators):
            K_dual = self.hodge_dual_operator(K, cache_key=f"kraus_{i}")
            dual_kraus.append(K_dual)
        return dual_kraus
