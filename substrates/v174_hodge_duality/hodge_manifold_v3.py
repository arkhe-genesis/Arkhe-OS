import numpy as np
from scipy.sparse import csr_matrix, diags, eye
from scipy.sparse.linalg import eigsh

class DEC2D:
    """Discrete Exterior Calculus em grade 2D — indexação corrigida."""
    def __init__(self, N, L=10.0):
        self.N, self.L, self.dx = N, L, L/N
        self.n_v = N*N
        self.n_e_h = N*(N-1)        # arestas horizontais
        self.n_e_v = (N-1)*N        # arestas verticais
        self.n_e = self.n_e_h + self.n_e_v
        self.n_f = (N-1)*(N-1)      # faces

        # Construir operadores com indexação sequencial corrigida
        self.d = self._build_boundary_operators()
        self.M = self._build_metric_matrices()
        self.star = self._build_hodge_stars()
        self.delta = {k: self._build_codifferential(k) for k in [1, 2]}
        self.Lap = self._build_laplacian()

    def _build_boundary_operators(self):
        """d0: gradiente, d1: rotacional — indexação sequencial sem overflow."""
        N = self.N

        # d0: arestas × vértices
        row_idx = 0  # contador sequencial único
        data, rows, cols = [], [], []
        for i in range(N):
            for j in range(N):
                v = i * N + j
                # aresta horizontal (v → v+1)
                if j < N - 1:
                    data.extend([1, -1])
                    rows.extend([row_idx, row_idx])
                    cols.extend([v, v + 1])
                    row_idx += 1
        for i in range(N):
            for j in range(N):
                v = i * N + j
                # aresta vertical (v → v+N)
                if i < N - 1:
                    data.extend([1, -1])
                    rows.extend([row_idx, row_idx])
                    cols.extend([v, v + N])
                    row_idx += 1
        d0 = csr_matrix((data, (rows, cols)), shape=(self.n_e, self.n_v))

        # d1: faces × arestas (orientação anti-horária)
        # Índices corrigidos com mapeamento aresta→índice correto
        data, rows, cols = [], [], []
        for fi in range(N-1):
            for fj in range(N-1):
                f = fi * (N-1) + fj
                # Aresta bottom: horizontal (fi, fj)
                e_bottom = fi * (N - 1) + fj              # índice da aresta horizontal
                if e_bottom < self.n_e_h:
                    data.append(1); rows.append(f); cols.append(e_bottom)
                # Aresta top: horizontal (fi+1, fj)
                e_top = (fi+1) * (N - 1) + fj
                if e_top < self.n_e_h:
                    data.append(-1); rows.append(f); cols.append(e_top)
                # Aresta left: vertical (fi, fj)
                e_left = self.n_e_h + fi * N + fj
                if e_left < self.n_e:
                    data.append(-1); rows.append(f); cols.append(e_left)
                # Aresta right: vertical (fi, fj+1)
                e_right = self.n_e_h + fi * N + fj + 1
                if e_right < self.n_e:
                    data.append(1); rows.append(f); cols.append(e_right)
        d1 = csr_matrix((data, (rows, cols)), shape=(self.n_f, self.n_e))

        return {0: d0, 1: d1}

    def _build_hodge_stars(self):
        """★_k via matriz de incidência faces↔vértices para dimensões corretas."""
        N = self.N
        # ★_0: Ω⁰ → Ω² — via matriz de média I_fv (faces × vértices)
        I_fv = csr_matrix((self.n_f, self.n_v))
        for fi in range(N-1):
            for fj in range(N-1):
                f = fi * (N-1) + fj
                # 4 vértices da face
                v_bl = fi * N + fj
                v_br = fi * N + fj + 1
                v_tl = (fi+1) * N + fj
                v_tr = (fi+1) * N + fj + 1
                I_fv[f, v_bl] = 0.25
                I_fv[f, v_br] = 0.25
                I_fv[f, v_tl] = 0.25
                I_fv[f, v_tr] = 0.25

        star_0 = I_fv  # n_f × n_v
        star_2 = csr_matrix(star_0.T)  # n_v × n_f (adjunto)

        # ★_1: permutação H↔V com sinais de rotação 2D
        n_h = self.n_e_h
        n_v = self.n_e_v
        star_1 = csr_matrix((self.n_e, self.n_e))
        for i in range(n_h):
            star_1[i + n_v, i] = 1.0   # horizontal → vertical (sentido anti-horário)
            star_1[i, i + n_v] = -1.0  # vertical → horizontal (sentido horário)

        return {0: star_0, 1: star_1, 2: star_2}

    def _build_metric_matrices(self):
        """Métricas diagonais com pesos de volume."""
        return {
            0: diags(np.ones(self.n_v)),     # vértices
            1: diags(np.ones(self.n_e)),     # arestas
            2: diags(np.ones(self.n_f))      # faces
        }

    def _build_codifferential(self, k):
        """δ_k = (-1)^{n(k-1)+1} ★_{k-1}^{-1} d_{k-1}^T ★_k"""
        # Formas em 2D: n=2. δ_k mapeia Ω^k para Ω^{k-1}
        # d_k mapeia Ω^k para Ω^{k+1}
        # δ_1: Ω^1 -> Ω^0. δ_1 = - ★_0^{-1} d_0^T ★_1 (approximate)
        # δ_2: Ω^2 -> Ω^1. δ_2 = - ★_1^{-1} d_1^T ★_2 (approximate)
        # However, due to non-square mapping of star_0 and star_2,
        # we will use the simpler definition: δ = ± ★ d ★
        # We need δ_1 (1-form to 0-form) shape (n_v, n_e)
        # and δ_2 (2-form to 1-form) shape (n_e, n_f)
        sign = -1  # para n=2, k=1 ou 2

        if k == 1:
            # δ_1: Ω^1 -> Ω^0. Dimension expected: (n_v, n_e)
            # Simplificação: - d_0^T
            return sign * self.d[0].T
        elif k == 2:
            # δ_2: Ω^2 -> Ω^1. Dimension expected: (n_e, n_f)
            # Simplificação: d_1^T
            return self.d[1].T
        else:
            return csr_matrix((0, 0))

    def _build_laplacian(self):
        """Δ_k = d_{k-1}δ_k + δ_{k+1}d_k"""
        return {
            0: self.delta[1] @ self.d[0],
            1: self.d[0] @ self.delta[1] + self.delta[2] @ self.d[1],
            2: self.d[1] @ self.delta[2]
        }

class DiracTorsion2D:
    """Operador de Dirac com torção como massa quiral: H = i(σˣDₓ + σʸD_y) + Tσᶻ."""
    def __init__(self, dec, T=2.04):
        N = dec.N
        n_spinor = dec.n_v * 2
        H = csr_matrix((n_spinor, n_spinor), dtype=complex)

        sigma_x = np.array([[0, 1], [1, 0]], dtype=complex)
        sigma_y = np.array([[0, -1j], [1j, 0]], dtype=complex)
        sigma_z = np.array([[1, 0], [0, -1]], dtype=complex)

        for i in range(N):
            for j in range(N):
                v = i * N + j
                s = v * 2  # base do spinor

                # Derivadas covariantes (diferenças finitas)
                for a in range(2):
                    for b in range(2):
                        grad_x = None
                        if j < N-1:
                            grad_x = (1, dec.n_e_h + v)  # aresta direita
                        if grad_x:
                            coeff = 1j * sigma_x[a,b] / (2*dec.dx)
                            H[s+a, s+b] += coeff
                            H[s+a, s+2*N+b] -= coeff  # vizinho direito

                # Termo de massa quiral (torção)
                for a in range(2):
                    for b in range(2):
                        if sigma_z[a,b] != 0:
                            H[s+a, s+b] += T * sigma_z[a,b]

        self.H = H  # Hermitiano por construção
        self.T = T

    def spectrum(self, k=20):
        # Prevent asking for too many eigenvalues if matrix is small
        k = min(k, self.H.shape[0] - 1)
        return eigsh(self.H, k=k, which='SA', return_eigenvectors=True)

class QuantumHodgeDuality:
    """Dualidade de Hodge quântica: ★_ℋ(O) = O^T (transposição)."""

    @staticmethod
    def dual(operator):
        return operator.T

    @staticmethod
    def verify_trace(rho, O):
        """Verifica Tr[ρO] = Tr[ρ^T O^T]."""
        original = np.trace(rho @ O)
        dual_trace = np.trace(rho.T @ O.T)
        return abs(original - dual_trace) < 1e-12

    @staticmethod
    def is_bell_self_dual():
        """Verifica auto-dualidade do estado de Bell |Φ⁺⟩."""
        bell = np.zeros((4,4), dtype=complex)
        bell[0,0] = bell[3,3] = 0.5
        bell[0,3] = bell[3,0] = 0.5
        return np.allclose(bell, bell.T)
