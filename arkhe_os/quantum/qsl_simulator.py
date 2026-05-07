import numpy as np
from scipy.linalg import expm

class KagomeQSLSimulator:
    """Simulador de Quantum Spin Liquid na rede kagome usando o formalismo Ψ_ToE."""

    def __init__(self, n_unit_cells: int = 12, J: float = 1.0):
        self.n = n_unit_cells
        self.N = n_unit_cells * 3  # 3 spins por célula unitária kagome
        self.J = J
        # Constrói a rede kagome (triângulos de canto compartilhado)
        self.triangles = self._build_kagome_triangles()
        # Inicializa estado RVB aleatório
        self.state = self._initialize_rvb_state()

    def _build_kagome_triangles(self) -> list:
        """Retorna lista de triângulos (cada triângulo = 3 índices de spin)."""
        triangles = []
        for i in range(self.n):
            base = 3 * i
            # Cada célula tem 2 triângulos: (0,1,2) e (1,2,3) com condições de contorno
            triangles.append([base, (base + 1) % self.N, (base + 2) % self.N])
            triangles.append([(base + 1) % self.N, (base + 2) % self.N, (base + 3) % self.N])
        return triangles

    def _initialize_rvb_state(self) -> np.ndarray:
        """Inicializa estado como superposição de singletos ressonantes."""
        # Estado simplificado: superposição uniforme com fases aleatórias
        psi = np.random.randn(2**self.N) + 1j * np.random.randn(2**self.N)
        return psi / np.linalg.norm(psi)

    def chiral_operator(self, triangle: list) -> np.ndarray:
        """Constrói operador de quiralidade χ_Δ para um triângulo."""
        dim = 2**self.N
        chi = np.zeros((dim, dim), dtype=complex)
        for state_idx in range(dim):
            bits = [(state_idx >> i) & 1 for i in range(self.N)]
            s1, s2, s3 = bits[triangle[0]], bits[triangle[1]], bits[triangle[2]]

            # Spin projection
            # To get a non-zero commutator we need off-diagonal elements in chi
            # Let's map directly to: χ = i(S+S+S+ - S-S-S-) / 2 as suggested in the problem context
            # Actually, the user prompt states:
            # χ_△ = S1 · (S2 × S3)
            # A simplified form the prompt provided had:
            # χ = (i/2) * (σ1^+ σ2^+ σ3^+ - σ1^- σ2^- σ3^-)

            if s1 == 0 and s2 == 0 and s3 == 0:
                # All spins down -> up
                new_state = state_idx | (1 << triangle[0]) | (1 << triangle[1]) | (1 << triangle[2])
                chi[new_state, state_idx] = 1j / 2.0
            elif s1 == 1 and s2 == 1 and s3 == 1:
                # All spins up -> down
                new_state = state_idx & ~(1 << triangle[0]) & ~(1 << triangle[1]) & ~(1 << triangle[2])
                chi[new_state, state_idx] = -1j / 2.0
        return chi

    def non_commutativity_measure(self) -> float:
        """Mede o grau de não-comutatividade espacial na rede inteira."""
        total_non_comm = 0.0
        pairs = 0
        for i, tri_i in enumerate(self.triangles):
            for j, tri_j in enumerate(self.triangles):
                if i >= j:
                    continue
                # Verifica se triângulos compartilham vértice (são adjacentes)
                if len(set(tri_i) & set(tri_j)) > 0:
                    chi_i = self.chiral_operator(tri_i)
                    chi_j = self.chiral_operator(tri_j)
                    commutator = chi_i @ chi_j - chi_j @ chi_i
                    total_non_comm += np.linalg.norm(commutator)
                    pairs += 1
        return total_non_comm / max(1, pairs)

    def spinon_excitation(self, momentum: np.ndarray) -> np.ndarray:
        """Cria excitação de spinon com momento k."""
        k_vector = momentum
        spinon_state = np.zeros_like(self.state)
        for i in range(self.N):
            phase = np.exp(1j * np.dot(k_vector, self._site_position(i)))
            # Aplica operador de criação de spinon simplificado
            sigma_plus = self._single_site_operator(i, 'plus')
            spinon_state += phase * (sigma_plus @ self.state)
        return spinon_state / np.linalg.norm(spinon_state)

    def _site_position(self, i: int) -> np.ndarray:
        """Retorna posição 2D do sítio i na rede kagome."""
        # Simplificação: coordenadas aproximadas
        cell = i // 3
        sublattice = i % 3
        x = cell + (0.5 if sublattice == 1 else 0)
        y = (sublattice * 0.577)  # altura do triângulo equilátero
        return np.array([x, y])

    def _single_site_operator(self, i: int, op_type: str) -> np.ndarray:
        """Constrói operador de spin no sítio i."""
        dim = 2**self.N
        op = np.zeros((dim, dim), dtype=complex)
        if op_type == 'plus':
            for state in range(dim):
                if not ((state >> i) & 1):  # spin down → up
                    new_state = state | (1 << i)
                    op[new_state, state] = 1.0
        elif op_type == 'minus':
            for state in range(dim):
                if (state >> i) & 1:  # spin up → down
                    new_state = state & ~(1 << i)
                    op[new_state, state] = 1.0
        elif op_type == 'z':
            for state in range(dim):
                if (state >> i) & 1:
                    op[state, state] = 1.0
                else:
                    op[state, state] = -1.0
        return op

    def compute_coherence(self) -> float:
        """Calcula Φ_C do QSL como fidelidade com estado RVB ideal."""
        # Projeta estado atual no subespaço RVB
        rvb_projection = self._project_to_rvb()
        fidelity = np.abs(np.dot(self.state.conj(), rvb_projection))
        return float(fidelity)

    def _project_to_rvb(self) -> np.ndarray:
        """Projeta estado no subespaço de singletos (RVB ideal)."""
        # Simplificação: projeção nos estados com magnetização total zero
        projected = np.zeros_like(self.state)
        for state_idx in range(2**self.N):
            bits = [(state_idx >> i) & 1 for i in range(self.N)]
            total_spin = sum(1 if b == 1 else -1 for b in bits)
            if total_spin == 0:  # Subespaço de magnetização nula
                projected[state_idx] = self.state[state_idx]
        norm = np.linalg.norm(projected)
        return projected / norm if norm > 0 else projected
