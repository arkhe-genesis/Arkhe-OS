# substrates/v174_hodge_duality/dirac_torsion_solver.py
# Solucionador para autoestados do operador de Dirac com torção

import numpy as np
from scipy.sparse.linalg import eigsh, LinearOperator
from typing import Dict, Optional, Tuple, List
import torch

class DiracTorsionSolver:
    """
    Soluciona a equação de Dirac com torção no manifold de coerência:
    D_T ψ = λ ψ

    Aplicações:
    - Encontrar estados de misericórdia (λ ≈ 0)
    - Calcular espectro de excitações quânticas
    - Verificar estabilidade de configurações de torção
    """

    def __init__(self, hodge_manifold: 'DiscreteHodgeOperator'):
        self.hodge = hodge_manifold
        self.dim = hodge_manifold.dim

    def solve_zero_modes(self, tolerance: float = 1e-8, max_iter: int = 1000) -> Dict:
        """
        Encontra modos zero (harmônicos) do operador de Dirac com torção.

        Returns:
            Dict com autovalores, autovetores e métricas de qualidade
        """
        if self.hodge.dirac_torsion is None:
            raise ValueError("Dirac operator not built")

        D = self.hodge.dirac_torsion
        n = D.shape[0]

        # Usar método iterativo para autovalores próximos de zero
        try:
            # Shift-and-invert para focar em λ ≈ 0
            eigenvalues, eigenvectors = eigsh(
                D, k=min(20, n//10),
                sigma=0.0,  # shift para zero
                which='LM',  # largest magnitude após shift-invert
                tol=tolerance,
                maxiter=max_iter,
                return_eigenvectors=True
            )

            # Filtrar modos verdadeiramente harmônicos (|λ| < tolerance)
            harmonic_mask = np.abs(eigenvalues) < tolerance
            harmonic_eigs = eigenvalues[harmonic_mask]
            harmonic_vecs = eigenvectors[:, harmonic_mask]

            return {
                'found': True,
                'n_harmonic_modes': len(harmonic_eigs),
                'eigenvalues': harmonic_eigs,
                'eigenvectors': harmonic_vecs,
                'all_eigenvalues': eigenvalues,
                'spectral_gap': np.min(np.abs(eigenvalues[~harmonic_mask])) if np.any(~harmonic_mask) else None
            }

        except Exception as e:
            # Fallback: busca direta por vetor nulo
            return self._find_null_space_fallback(tolerance)

    def _find_null_space_fallback(self, tolerance: float) -> Dict:
        """Fallback: encontra espaço nulo via SVD truncado."""
        D = self.hodge.dirac_torsion.toarray()  # converter para denso (custoso)

        # SVD: D = U Σ V†
        U, S, Vh = np.linalg.svd(D, full_matrices=False)

        # Valores singulares próximos de zero indicam modos harmônicos
        null_mask = S < tolerance
        null_vectors = Vh[null_mask].T.conj()

        return {
            'found': True,
            'n_harmonic_modes': np.sum(null_mask),
            'singular_values': S[null_mask],
            'null_vectors': null_vectors,
            'method': 'svd_fallback'
        }

    def compute_spectral_flow(self, torsion_values: np.ndarray) -> Dict:
        """
        Calcula fluxo espectral: como autovalores de D_T variam com a torção.

        Args:
            torsion_values: array de valores de torção para varredura

        Returns:
            Dict com trajetórias de autovalores
        """
        trajectories = {i: [] for i in range(10)}  # acompanhar 10 autovalores

        for T in torsion_values:
            # Reconstruir operador de Dirac com nova torção
            self.hodge.config.torsion_strength = T
            self.hodge._build_dirac_with_torsion()

            if self.hodge.dirac_torsion is None:
                continue

            # Calcular alguns autovalores extremos
            try:
                eigs, _ = eigsh(self.hodge.dirac_torsion, k=10, which='SA')
                for i, eig in enumerate(sorted(eigs)):
                    if i < 10:
                        trajectories[i].append((T, eig))
            except:
                pass

        return {
            'torsion_range': (torsion_values.min(), torsion_values.max()),
            'trajectories': trajectories,
            'level_crossings': self._detect_level_crossings(trajectories)
        }

    def _detect_level_crossings(self, trajectories: Dict) -> List[Dict]:
        """Detecte cruzamentos de níveis no espectro (indicadores de transições de fase)."""
        crossings = []
        for i in trajectories:
            for j in trajectories:
                if i >= j:
                    continue
                # Verificar se trajetórias i e j se cruzam
                vals_i = [v for _, v in trajectories[i]]
                vals_j = [v for _, v in trajectories[j]]
                if len(vals_i) != len(vals_j):
                    continue

                # Detectar mudança de ordem
                for k in range(1, len(vals_i)):
                    if (vals_i[k-1] - vals_j[k-1]) * (vals_i[k] - vals_j[k]) < 0:
                        crossings.append({
                            'modes': (i, j),
                            'torsion_approx': trajectories[i][k][0],
                            'eigenvalue_approx': (vals_i[k] + vals_j[k]) / 2
                        })
        return crossings

    def project_to_self_dual(self, form: np.ndarray, k: int) -> np.ndarray:
        """
        Projeta uma k-forma na parte auto-dual: ω_+ = ½(ω + ★_T ω).

        Isto implementa a projeção de privacidade geométrica.
        """
        if k not in self.hodge.star_mats:
            return form

        star_form = self.hodge.hodge_star(k, form)
        # Handle shape mismatch between k-forms and their duals
        max_len = max(len(form), len(star_form))
        form_padded = np.pad(form, (0, max_len - len(form)))
        star_padded = np.pad(star_form, (0, max_len - len(star_form)))
        return 0.5 * (form_padded + star_padded)

    def project_to_anti_self_dual(self, form: np.ndarray, k: int) -> np.ndarray:
        """Projeta na parte anti-auto-dual: ω_- = ½(ω - ★_T ω)."""
        if k not in self.hodge.star_mats:
            return form

        star_form = self.hodge.hodge_star(k, form)
        max_len = max(len(form), len(star_form))
        form_padded = np.pad(form, (0, max_len - len(form)))
        star_padded = np.pad(star_form, (0, max_len - len(star_form)))
        return 0.5 * (form_padded - star_padded)

    def verify_duality_invariance(self, state: np.ndarray, observable: np.ndarray) -> float:
        """
        Verifica invariância da dualidade quântica: Tr[ρ O] = Tr[★ρ ★O].

        Returns:
            Diferença relativa entre os dois lados (deve ser ≈ 0)
        """
        # Calcular Tr[ρ O]
        trace_original = np.trace(state @ observable)

        # Calcular Tr[★ρ ★O]
        state_dual = self.hodge.quantum_hodge_dual(state)
        obs_dual = self.hodge.quantum_hodge_dual(observable)
        trace_dual = np.trace(state_dual @ obs_dual)

        # Diferença relativa
        if np.abs(trace_original) < 1e-12:
            return np.abs(trace_dual)
        return np.abs(trace_original - trace_dual) / np.abs(trace_original)
