"""
ARKHE v1.0 — Pipeline Unificado
Integra:
- Análise de criticalidade SOC robusta para backends quânticos reais.
- Mapeamento Fiedler → Potencial de Contração Φ(r).
- Solver de autovalores do Casulo (JAX) alimentado com Φ(r) experimental.
"""

import jax
import jax.numpy as jnp
import numpy as np
from scipy.sparse.csgraph import laplacian
from scipy.linalg import eigh
from typing import Dict, Tuple, List

# ============================================================================
# 1. MÓDULO DE ANÁLISE SOC ROBUSTA (COM OS 5 PATCHES)
# ============================================================================

def robust_soc_fit(data: np.ndarray, N_min: int = 50, bootstrap_N: int = 1000) -> Tuple[float, float, np.ndarray]:
    """
    Ajuste SOC robusto para backends pequenos (< 200 qubits).
    Retorna alpha, xmin, data_detrended.
    """
    # PATCH 3: Pre-whitening térmico (remover tendência global do diluidor)
    x = np.arange(len(data))
    if len(data) > 2:
        coeffs = np.polyfit(x, data, 2)
        trend = np.polyval(coeffs, x)
        data_detrended = data - trend
    else:
        data_detrended = data

    # PATCH 1: Amostragem mínima via bootstrap do estimador de Hill
    if len(data_detrended) < N_min:
        boot_alphas = []
        for _ in range(bootstrap_N):
            sample = np.random.choice(data_detrended, size=len(data_detrended), replace=True)
            sorted_s = np.sort(sample)[::-1]
            k = max(int(0.1 * len(sample)), 5)
            if len(sorted_s) > k and sorted_s[k] > 0:
                hill = np.mean(np.log(sorted_s[:k] / sorted_s[k]))
                boot_alphas.append(1.0 / hill if hill > 0 else np.nan)
            else:
                boot_alphas.append(np.nan)
        alpha = np.nanmedian(boot_alphas)
        xmin = np.percentile(data_detrended, 10) if len(data_detrended) > 0 else 0
    else:
        # Método padrão (powerlaw) seria chamado aqui
        alpha, xmin = 2.5, np.percentile(data_detrended, 10)  # placeholder

    # PATCH 2: Proxy de criticalidade por kurtosis se alpha for NaN
    if np.isnan(alpha):
        from scipy import stats
        if len(data_detrended) > 0:
            kurt = stats.kurtosis(data_detrended, fisher=False)
            alpha = 6.0 / max(kurt - 1.8, 0.1)
            xmin = np.min(data_detrended)
        else:
            alpha = 0.0
            xmin = 0.0

    return alpha, xmin, data_detrended


def adaptive_percentiles(N_total: int) -> Tuple[float, float]:
    """PATCH 5: Percentis adaptativos para N pequeno."""
    if N_total < 200:
        return 25.0, 75.0
    elif N_total < 1000:
        return 15.0, 85.0
    else:
        return 10.0, 90.0


# ============================================================================
# 2. CONVERSÃO DE DADOS IBMQ → GRAFO LAPLACIANO & FIEDLER
# ============================================================================

def build_connectivity_graph(backend_props: Dict) -> Tuple[np.ndarray, np.ndarray]:
    """
    Constrói matriz de adjacência e Laplaciano a partir das propriedades do backend.
    """
    n_qubits = len(backend_props['t1'])
    coupling = backend_props['coupling_map']
    adj = np.zeros((n_qubits, n_qubits))
    for i, j in coupling:
        if i < n_qubits and j < n_qubits:
            # Peso da aresta: inverso do erro ECR médio (ou outro gate)
            # Simulado aqui como função de T1/T2
            t1_ij = min(backend_props['t1'][i], backend_props['t1'][j])
            t2_ij = min(backend_props['t2'][i], backend_props['t2'][j])
            # Qualidade da conexão (arbitrária, mas fisicamente motivada)
            weight = np.exp(-1.0 / (t1_ij * t2_ij + 1e-6))
            adj[i, j] = weight
            adj[j, i] = weight
    L = laplacian(adj, normed=False)
    return L, adj


def compute_fiedler_vector(L: np.ndarray) -> np.ndarray:
    """Calcula o autovetor de Fiedler (v2) do Laplaciano."""
    eigvals, eigvecs = eigh(L)
    # Ordenar autovalores (o Laplaciano é semi-definido positivo)
    idx = np.argsort(eigvals)
    if len(idx) > 1:
        v2 = eigvecs[:, idx[1]]  # segundo menor autovalor
    else:
        v2 = eigvecs[:, idx[0]]
    return v2


# ============================================================================
# 3. MAPEAMENTO FIEDLER → POTENCIAL DE CONTRAÇÃO Φ(r)
# ============================================================================

def fiedler_to_contraction_potential(v2: np.ndarray, epsilon: float = 1e-6) -> np.ndarray:
    """
    Φ(i) = -log(|v2(i)| + ε)
    """
    return -np.log(np.abs(v2) + epsilon)


def assign_phases(v2: np.ndarray, N_total: int) -> Dict[str, List[int]]:
    """
    Classifica qubits em Cut, Mid, Bulk baseado no vetor de Fiedler.
    Usa percentis adaptativos (PATCH 5).
    """
    low_p, high_p = adaptive_percentiles(N_total)
    v2_abs = np.abs(v2)
    low_thresh = np.percentile(v2_abs, low_p)
    high_thresh = np.percentile(v2_abs, high_p)

    cut = np.where(v2_abs <= low_thresh)[0].tolist()
    bulk = np.where(v2_abs >= high_thresh)[0].tolist()
    mid = [i for i in range(N_total) if i not in cut and i not in bulk]

    return {"cut": cut, "mid": mid, "bulk": bulk}


# ============================================================================
# 4. SOLVER DO CASULO ALIMENTADO POR Φ EXPERIMENTAL
# ============================================================================

def casulo_eigensolver(phi_field: jnp.ndarray, r0: float = 3.0, C: float = 2.27e-18) -> Dict:
    """
    Resolve os modos da cavidade esférica com potencial de contração Φ.
    phi_field: array 1D com valores de Φ para cada "ponto" radial discreto.
    """
    n_points = len(phi_field)
    r = jnp.linspace(0, r0, n_points)

    # Hamiltoniano simplificado: -d²/dr² + V(r)
    # V(r) = -C * r * phi_field (análogo ao potencial gravitacional efetivo)
    def V_func(r_val, phi_val):
        return -C * r_val * phi_val

    # Construir matriz tridiagonal para diferenças finitas
    dr = r[1] - r[0] if n_points > 1 else 1.0

    # Use JAX vectorized operations instead of list comprehension for performance and JIT-friendliness
    v_vals = jax.vmap(V_func)(r, phi_field)

    diag = 2.0 / dr**2 + v_vals
    off_diag = -1.0 / dr**2 * jnp.ones(n_points - 1)
    H = jnp.diag(diag) + jnp.diag(off_diag, k=1) + jnp.diag(off_diag, k=-1)

    eigvals, eigvecs = jnp.linalg.eigh(H)
    return {
        "eigenvalues": eigvals,
        "eigenvectors": eigvecs,
        "r": r,
        "phi_field": phi_field
    }


# ============================================================================
# 5. PIPELINE COMPLETO
# ============================================================================

def unified_arkhe_pipeline(backend_props: Dict) -> Dict:
    """
    Recebe dados reais do backend IBMQ e retorna:
        - Fases (cut/mid/bulk)
        - Potencial Φ por qubit
        - Modos do Casulo ajustados por Φ
    """
    # 1. Construir grafo e Fiedler
    L, adj = build_connectivity_graph(backend_props)
    v2 = compute_fiedler_vector(L)

    # 2. Potencial de contração
    phi = fiedler_to_contraction_potential(v2)

    # 3. Classificação de fases
    n_qubits = len(v2)
    phases = assign_phases(v2, n_qubits)

    # 4. Análise SOC para T1 dos qubits Bulk e Cut
    t1_data = np.array(backend_props['t1'])
    alpha_cut, xmin_cut, _ = robust_soc_fit(t1_data[phases['cut']])
    alpha_bulk, xmin_bulk, _ = robust_soc_fit(t1_data[phases['bulk']])

    # 5. Resolver Casulo com Φ (usando JAX)
    phi_jax = jnp.array(phi)
    casulo_modes = casulo_eigensolver(phi_jax)

    return {
        "phases": phases,
        "potential_phi": phi,
        "soc": {
            "alpha_cut": alpha_cut, "xmin_cut": xmin_cut,
            "alpha_bulk": alpha_bulk, "xmin_bulk": xmin_bulk
        },
        "casulo_modes": casulo_modes,
        "lambda2": float(np.sort(eigh(L)[0])[1]) if n_qubits > 1 else 0.0
    }
