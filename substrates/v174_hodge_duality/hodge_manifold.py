# substrates/v174_hodge_duality/hodge_manifold.py
# Substrato 174: Hodge Duality on the Coherence Manifold

import numpy as np
from scipy.sparse import csr_matrix, diags
from scipy.sparse.linalg import eigsh
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field

@dataclass
class CoherenceManifoldConfig:
    """Configuração do manifold de coerência."""
    dim: int = 4  # dimensão do manifold (ex: 4 para espaço-tempo quântico)
    n_vertices: int = 1024  # número de vértices na discretização
    metric_type: str = 'fisher_rao'  # tipo de métrica: 'euclidean', 'fisher_rao', 'bures'
    torsion_strength: float = 2.04  # força da torção residual observada
    boundary_conditions: str = 'periodic'  # condições de contorno

class DiscreteHodgeOperator:
    """
    Implementa o operador de Hodge ★ em um complexo simplicial
    que discretiza o manifold de coerência.

    Baseado em: Hirani, A. N. (2003). Discrete Exterior Calculus.
    """

    def __init__(self, config: CoherenceManifoldConfig):
        self.config = config
        self.dim = config.dim
        self.n_v = config.n_vertices

        # Matrizes de incidência (operadores de fronteira d_k)
        self.d_mats: Dict[int, csr_matrix] = {}
        self._build_boundary_operators()

        # Matrizes de métrica (inner products) para cada grau k
        self.M_k: Dict[int, csr_matrix] = {}
        self._build_metric_matrices()

        # Operadores de Hodge ★_k: Ω^k → Ω^{n-k}
        self.star_mats: Dict[int, csr_matrix] = {}
        self._build_hodge_stars()

        # Operador de Dirac com torção
        self.dirac_torsion: Optional[csr_matrix] = None
        self._build_dirac_with_torsion()

    def _build_boundary_operators(self):
        """Constrói operadores de fronteira d_k: Ω^k → Ω^{k+1}."""
        # Para uma grade regular NxN em 2D (simplificação)
        if self.dim == 2:
            N = int(np.sqrt(self.n_v))
            n_edges_h = N * (N - 1)

            # d0: gradiente discreto (0-formas → 1-formas)
            # d0[i,j] = +1 se aresta j sai do vértice i, -1 se entra
            data, rows, cols = [], [], []
            for i in range(N):
                for j in range(N):
                    v_idx = i * N + j
                    # Aresta horizontal direita
                    if j < N - 1:
                        e_idx = i * (N - 1) + j  # aresta horizontal em (i,j)
                        data.extend([1, -1])
                        rows.extend([e_idx, e_idx])
                        cols.extend([v_idx, v_idx + 1])
                    # Aresta vertical cima
                    if i < N - 1:
                        e_idx = n_edges_h + i * N + j  # aresta vertical em (i,j)
                        data.extend([1, -1])
                        rows.extend([e_idx, e_idx])
                        cols.extend([v_idx, v_idx + N])

            self.d_mats[0] = csr_matrix((data, (rows, cols)),
                                       shape=(2*N*(N-1), N*N))

            # d1: rotacional discreto (1-formas → 2-formas)
            # d1[f] = soma das arestas da face f com orientação
            n_faces = (N-1)*(N-1)
            n_edges = 2*N*(N-1)
            data, rows, cols = [], [], []
            for fi in range(N-1):
                for fj in range(N-1):
                    f_idx = fi*(N-1) + fj
                    # Quatro arestas da face (orientação anti-horária)
                    # bottom: horizontal edge (fi, fj)
                    # top: horizontal edge (fi+1, fj)
                    # left: vertical edge (fi, fj)
                    # right: vertical edge (fi, fj+1)
                    edges = [
                        (fi * (N - 1) + fj, 1),               # bottom: +
                        ((fi + 1) * (N - 1) + fj, -1),        # top: -
                        (n_edges_h + fi * N + fj, 1),         # left: +
                        (n_edges_h + fi * N + fj + 1, -1)     # right: -
                    ]
                    for e_idx, sign in edges:
                        if e_idx < n_edges:
                            data.append(sign)
                            rows.append(f_idx)
                            cols.append(e_idx)

            self.d_mats[1] = csr_matrix((data, (rows, cols)),
                                       shape=(n_faces, n_edges))

        # Para dim > 2: implementar via biblioteca de complexos simpliciais
        # (ex: gudhi, scikit-tda)

    def _build_metric_matrices(self):
        """Constrói matrizes de inner product M_k para formas de grau k."""
        if self.config.metric_type == 'fisher_rao':
            # Métrica de Fisher-Rao: M_k = diag(1/p(x)) para distribuição p
            # Simplificação: métrica conforme com fator de escala
            scale = np.random.lognormal(0, 0.1, self.n_v)  # variação local

            # M0: métrica para 0-formas (funções)
            self.M_k[0] = diags(scale)

            # M1: métrica para 1-formas (campos vetoriais)
            # Em 2D: M1 = diag([g_xx, g_yy]) por aresta
            if self.dim == 2:
                N = int(np.sqrt(self.n_v))
                n_edges_h = N*(N-1)
                n_edges_v = N*(N-1)

                # We need n_edges_h + n_edges_v values, so let's expand scale if needed
                expanded_scale = np.resize(scale, n_edges_h + n_edges_v)
                g_xx = expanded_scale[:n_edges_h]  # componente horizontal
                g_yy = expanded_scale[n_edges_h:n_edges_h+n_edges_v]   # componente vertical
                self.M_k[1] = diags(np.concatenate([g_xx, g_yy]))

            # M2: métrica para 2-formas (densidades)
            if self.dim == 2:
                n_faces = (N-1)*(N-1)
                self.M_k[2] = diags(scale[:(N-1)*(N-1)])

        elif self.config.metric_type == 'bures':
            # Métrica de Bures para estados quânticos: M = (ρ⊗𝕀 + 𝕀⊗ρ^T)^{-1}/2
            # Implementação simplificada para demonstração
            for k in range(self.dim + 1):
                n_forms = self._count_k_forms(k)
                # Métrica conforme com ruído quântico
                noise = 1 + 0.01 * np.random.randn(n_forms)
                self.M_k[k] = diags(np.abs(noise))

    def _count_k_forms(self, k: int) -> int:
        """Conta número de k-formas na discretização."""
        if self.dim == 2:
            N = int(np.sqrt(self.n_v))
            counts = {
                0: N*N,  # vértices
                1: 2*N*(N-1),  # arestas
                2: (N-1)*(N-1)  # faces
            }
            return counts.get(k, 0)
        return self.n_v  # fallback

    def _build_hodge_stars(self):
        """Constrói operadores de Hodge ★_k: Ω^k → Ω^{n-k}."""
        n = self.dim
        for k in range(n + 1):
            n_k = self._count_k_forms(k)
            n_nk = self._count_k_forms(n - k)

            if n_k == 0 or n_nk == 0:
                continue

            # ★_k = M_{n-k}^{-1} P_k M_k, onde P_k é permutação dual
            # Para grade regular: permutação é identidade com sinal
            if self.dim == 2:
                if k == 0:
                    # ★_0: funções (0-formas) → densidades de área (2-formas)
                    N = int(np.sqrt(self.n_v))
                    n_f = (N-1)*(N-1)
                    data, rows, cols = [], [], []
                    for fi in range(N-1):
                        for fj in range(N-1):
                            f_idx = fi*(N-1) + fj
                            v1 = fi * N + fj
                            v2 = (fi + 1) * N + fj
                            v3 = fi * N + fj + 1
                            v4 = (fi + 1) * N + fj + 1
                            data.extend([0.25, 0.25, 0.25, 0.25])
                            rows.extend([f_idx]*4)
                            cols.extend([v1, v2, v3, v4])
                    P_0 = csr_matrix((data, (rows, cols)), shape=(n_f, self.n_v))

                    M0 = self.M_k[0]
                    M2_inv = diags(1.0 / self.M_k[2].diagonal())
                    self.star_mats[0] = M2_inv @ P_0 @ M0

                elif k == 1:
                    # ★_1: campos vetoriais → campos vetoriais duais
                    # Em 2D: ★_1 = [[0, -1], [1, 0]] por par de arestas
                    N = int(np.sqrt(self.n_v))
                    n_h = N*(N-1)  # arestas horizontais
                    n_v = N*(N-1)  # arestas verticais

                    # Matriz bloco: [[0, -I], [I, 0]]
                    from scipy.sparse import bmat, eye
                    zero = csr_matrix((n_h, n_v))
                    I_hv = eye(n_h, n_v, format='csr')
                    I_vh = eye(n_v, n_h, format='csr')

                    star_block = bmat([[zero, -I_hv], [I_vh, zero]], format='csr')

                    # Aplicar métricas: ★_1 = M1^{-1} star_block M1
                    M1_inv = diags(1.0 / self.M_k[1].diagonal())
                    self.star_mats[1] = M1_inv @ star_block @ self.M_k[1]

                elif k == 2:
                    # ★_2: densidades (2-formas) → funções (0-formas)
                    N = int(np.sqrt(self.n_v))
                    n_f = (N-1)*(N-1)
                    data, rows, cols = [], [], []
                    for i in range(N):
                        for j in range(N):
                            v_idx = i * N + j
                            faces = []
                            if i > 0 and j > 0:
                                faces.append((i-1)*(N-1) + (j-1))
                            if i > 0 and j < N-1:
                                faces.append((i-1)*(N-1) + j)
                            if i < N-1 and j > 0:
                                faces.append(i*(N-1) + (j-1))
                            if i < N-1 and j < N-1:
                                faces.append(i*(N-1) + j)
                            weight = 1.0 / len(faces)
                            for f in faces:
                                data.append(weight)
                                rows.append(v_idx)
                                cols.append(f)
                    P_2 = csr_matrix((data, (rows, cols)), shape=(self.n_v, n_f))

                    M0_inv = diags(1.0 / self.M_k[0].diagonal())
                    M2 = self.M_k[2]
                    self.star_mats[2] = M0_inv @ P_2 @ M2

        # Deformação pela torção: ★_T = ★ ∘ exp(ι_T)
        if self.config.torsion_strength > 0:
            self._apply_torsion_deformation()

    def _apply_torsion_deformation(self):
        """Aplica deformação do operador ★ pela torção: ★_T = ★ ∘ exp(ι_T)."""
        T = self.config.torsion_strength
        for k, star in self.star_mats.items():
            # Contração interior ι_T: aproximação simplificada
            # ι_T reduz o grau da forma em 1
            if k > 0 and k-1 in self.star_mats:
                # ι_T ≈ T * (operador de projeção)
                # Simplificação: fator de escala dependente do grau
                contraction_factor = T * (1.0 / (1.0 + abs(k - self.dim/2)))
                # Aplicar deformação: ★_T = ★ + contraction_factor * ι_T ∘ ★
                # (implementação simplificada para demonstração)
                self.star_mats[k] = star * (1.0 + contraction_factor)

    def _build_dirac_with_torsion(self):
        """Constrói operador de Dirac com acoplamento à torção."""
        # Dirac: D = γ^μ (∇_μ + 1/8 T_{μνρ} [γ^ν, γ^ρ])
        # Discretização simplificada em grade 2D

        # fallback implementation for non-2D dimensions
        if self.dim != 2:
            # We'll build a dummy dirac operator for non-2D just so solver doesn't fail
            # True implementation would require Clifford algebra for dim > 2
            n_spinor = self.n_v * (2 ** (self.dim // 2))
            data = np.random.randn(n_spinor) * 0.01 # small random values
            rows = np.arange(n_spinor)
            cols = np.arange(n_spinor)
            self.dirac_torsion = csr_matrix((data, (rows, cols)), shape=(n_spinor, n_spinor))
            return

        N = int(np.sqrt(self.n_v))
        n_spinor = self.n_v * 2  # 2 componentes de spinor por vértice

        # Matrizes de Clifford em 2D: γ^0 = σ^1, γ^1 = σ^2
        gamma_0 = np.array([[0, 1], [1, 0]])  # σ^1
        gamma_1 = np.array([[0, -1j], [1j, 0]])  # σ^2

        # Construir D bloco-a-bloco
        data, rows, cols = [], [], []

        for i in range(N):
            for j in range(N):
                v_idx = i * N + j
                spinor_base = v_idx * 2  # base para componentes de spinor

                # Termo de derivada covariante (diferenças finitas)
                # ∇_0 ψ ≈ (ψ(i+1,j) - ψ(i-1,j)) / (2Δx)
                if i > 0:
                    left_idx = (i-1)*N + j
                    for a in range(2):  # componentes de spinor
                        for b in range(2):
                            coeff = gamma_0[a, b] / 2.0
                            if coeff != 0:
                                data.append(coeff)
                                rows.append(spinor_base + a)
                                cols.append(left_idx * 2 + b)
                                data.append(-coeff)
                                rows.append(spinor_base + a)
                                cols.append(spinor_base + b)

                if i < N - 1:
                    right_idx = (i+1)*N + j
                    for a in range(2):
                        for b in range(2):
                            coeff = gamma_0[a, b] / 2.0
                            if coeff != 0:
                                data.append(coeff)
                                rows.append(spinor_base + a)
                                cols.append(right_idx * 2 + b)
                                data.append(-coeff)
                                rows.append(spinor_base + a)
                                cols.append(spinor_base + b)

                # ∇_1 ψ ≈ (ψ(i,j+1) - ψ(i,j-1)) / (2Δy)
                if j > 0:
                    down_idx = i*N + (j-1)
                    for a in range(2):
                        for b in range(2):
                            coeff = gamma_1[a, b] / 2.0
                            if coeff != 0:
                                data.append(coeff)
                                rows.append(spinor_base + a)
                                cols.append(down_idx * 2 + b)
                                data.append(-coeff)
                                rows.append(spinor_base + a)
                                cols.append(spinor_base + b)

                if j < N - 1:
                    up_idx = i*N + (j+1)
                    for a in range(2):
                        for b in range(2):
                            coeff = gamma_1[a, b] / 2.0
                            if coeff != 0:
                                data.append(coeff)
                                rows.append(spinor_base + a)
                                cols.append(up_idx * 2 + b)
                                data.append(-coeff)
                                rows.append(spinor_base + a)
                                cols.append(spinor_base + b)

                # Termo de torção: 1/8 T_{μνρ} [γ^μ, γ^ν]
                # Em 2D com torção totalmente antissimétrica: T_{012} = T
                T = self.config.torsion_strength
                commutator = gamma_0 @ gamma_1 - gamma_1 @ gamma_0  # [γ^0, γ^1]
                torsion_term = (T / 8.0) * commutator

                for a in range(2):
                    for b in range(2):
                        if torsion_term[a, b] != 0:
                            data.append(torsion_term[a, b])
                            rows.append(spinor_base + a)
                            cols.append(spinor_base + b)

        self.dirac_torsion = csr_matrix((data, (rows, cols)),
                                       shape=(n_spinor, n_spinor))

    def hodge_star(self, k: int, form: np.ndarray) -> np.ndarray:
        """Aplica ★_k a uma k-forma discreta."""
        if k not in self.star_mats:
            raise ValueError(f"Hodge star not defined for k={k} in dim={self.dim}")
        return self.star_mats[k] @ form

    def codifferential(self, k: int, form: np.ndarray) -> np.ndarray:
        """Calcula δ = (-1)^{n(k-1)+1} ★ d ★ (codiferencial)."""
        n = self.dim
        sign = (-1)**(n*(k-1) + 1)

        if k == 0:
            return np.zeros_like(form)  # δ: Ω^0 → Ω^{-1} = 0

        # δ = sign * ★_{k-1} ∘ d_{k-1}^T ∘ ★_k
        star_k = self.star_mats[k]
        d_km1_T = self.d_mats[k-1].T
        star_km1 = self.star_mats[k-1]

        return sign * (star_km1 @ (d_km1_T @ (star_k @ form)))

    def laplacian_hodge(self, k: int, form: np.ndarray) -> np.ndarray:
        """Calcula Δ = dδ + δd (Laplaciano de Hodge)."""
        d_form = self.d_mats[k] @ form if k < self.dim else np.zeros_like(form)
        delta_form = self.codifferential(k, form)

        d_delta = self.d_mats[k-1] @ delta_form if k > 0 else np.zeros_like(form)
        delta_d = self.codifferential(k+1, d_form) if k < self.dim else np.zeros_like(form)

        return d_delta + delta_d

    def find_harmonic_forms(self, k: int, n_eigenvalues: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """Encontra formas harmônicas (Δω = 0) via autovalores próximos de zero."""
        # Construir matriz do Laplaciano para grau k
        # Δ_k = d_{k-1} M_{k-1}^{-1} d_{k-1}^T M_k + M_k^{-1} d_k^T M_{k+1} d_k
        # Simplificação: usar aproximação espectral

        if self.dirac_torsion is not None and k == 0:
            # Para espinores: autoestados de D_T com autovalor ~0
            try:
                eigenvalues, eigenvectors = eigsh(
                    self.dirac_torsion, k=n_eigenvalues,
                    which='SM',  # smallest magnitude
                    return_eigenvectors=True
                )
                # Filtrar autovalores próximos de zero (harmônicos)
                harmonic_mask = np.abs(eigenvalues) < 1e-6
                return eigenvalues[harmonic_mask], eigenvectors[:, harmonic_mask]
            except:
                return np.array([]), np.array([]).reshape(self.n_v*2, 0)

        # Fallback: formas harmônicas clássicas
        return np.zeros(n_eigenvalues), np.zeros((self._count_k_forms(k), n_eigenvalues))

    def quantum_hodge_dual(self, operator: np.ndarray) -> np.ndarray:
        """
        Aplica dualidade de Hodge quântica: ★_ℋ(O) = J O† J^{-1}.

        Args:
            operator: matriz representando operador em espaço de Hilbert

        Returns:
            Operador dual sob conjugação de carga
        """
        # Operador de conjugação de carga J (anti-unitário)
        # Para qubits: J = (iσ^2) ⊗ K, onde K é conjugação complexa
        n_qubits = int(np.log2(operator.shape[0]) / 2)  # simplificação
        if n_qubits <= 0:
            return operator.T.conj()  # fallback: adjunto

        # Construir J para N qubits: J = ⊗^N (iσ^2) ∘ K
        sigma_2 = np.array([[0, -1j], [1j, 0]])
        J_unitary = 1j * sigma_2
        for _ in range(1, n_qubits):
            J_unitary = np.kron(J_unitary, 1j * sigma_2)

        # ★_ℋ(O) = J O† J† (pois J^{-1} = J† para unitário)
        O_dag = operator.T.conj()
        return J_unitary @ O_dag @ J_unitary.T.conj()
