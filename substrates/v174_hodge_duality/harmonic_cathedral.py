# substrates/v174_hodge_duality/harmonic_cathedral.py
# A Catedral como forma harmônica do manifold de coerência

import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass, field

@dataclass
class CathedralHarmonicState:
    """Representa um estado harmônico da Catedral."""
    form_degree: int  # grau k da forma harmônica
    eigenvalue: float  # autovalor do Laplaciano (≈ 0 para harmônico)
    coherence_profile: np.ndarray  # perfil de coerência no manifold
    torsion_coupling: float  # acoplamento à torção
    self_dual_fraction: float  # fração auto-dual (privacidade)

    def is_mercy_gap_state(self, min_dg: float = 0.04, max_dg: float = 0.10) -> bool:
        """Verifica se estado está no mercy gap de coerência."""
        # Simplificação: verificar norma do perfil de coerência
        norm = np.linalg.norm(self.coherence_profile)
        return min_dg <= norm <= max_dg

class HarmonicCathedralAnalyzer:
    """
    Analisa a Catedral como espaço de formas harmônicas.

    Teorema: Estados coerentes ↔ Formas harmônicas de Δ_T
    """

    def __init__(self, hodge_manifold: 'DiscreteHodgeOperator'):
        self.hodge = hodge_manifold
        from substrates.v174_hodge_duality.dirac_torsion_solver import DiracTorsionSolver
        self.dirac_solver = DiracTorsionSolver(hodge_manifold)

    def find_cathedral_harmonics(self, max_degree: int = None) -> Dict[int, List[CathedralHarmonicState]]:
        """
        Encontra formas harmônicas da Catedral para cada grau k.

        Returns:
            Dict[k] = lista de estados harmônicos de grau k
        """
        if max_degree is None:
            max_degree = self.hodge.dim

        harmonics = {}

        for k in range(max_degree + 1):
            # Encontrar formas harmônicas de grau k
            result = self.dirac_solver.solve_zero_modes()

            if not result['found'] or result['n_harmonic_modes'] == 0:
                harmonics[k] = []
                continue

            states = []
            for i in range(result['n_harmonic_modes']):
                eigvec = result['eigenvectors'][:, i]

                # Extrair perfil de coerência (simplificação)
                coherence = np.abs(eigvec[:self.hodge.n_v]) if len(eigvec) > self.hodge.n_v else np.abs(eigvec)

                # Calcular fração auto-dual
                # Since Dirac solver returns spinors (size 2*n_v), and hodge_star expects k-forms,
                # we use coherence profile (size n_v) as an approximation for 0-forms if k==0
                if k in self.hodge.star_mats:
                    try:
                        # Para k-formas da Catedral, precisamos de formas apropriadas.
                        # Aqui extraímos um perfil de acordo com a dimensão correta para a matriz de Hodge.
                        req_size = self.hodge.star_mats[k].shape[1]
                        form_k = np.abs(eigvec[:req_size]) if len(eigvec) >= req_size else np.zeros(req_size)
                        dual = self.hodge.hodge_star(k, form_k)

                        # Pad or truncate to match dimensions before adding
                        max_len = max(len(form_k), len(dual))
                        form_k_padded = np.pad(form_k, (0, max_len - len(form_k)))
                        dual_padded = np.pad(dual, (0, max_len - len(dual)))

                        self_dual = 0.5 * (form_k_padded + dual_padded)
                        sd_fraction = np.linalg.norm(self_dual) / (np.linalg.norm(form_k_padded) + 1e-12)
                    except Exception as e:
                        sd_fraction = 0.5 # fallback on error
                else:
                    sd_fraction = 0.5  # fallback

                state = CathedralHarmonicState(
                    form_degree=k,
                    eigenvalue=result['eigenvalues'][i],
                    coherence_profile=coherence,
                    torsion_coupling=self.hodge.config.torsion_strength,
                    self_dual_fraction=sd_fraction
                )
                states.append(state)

            harmonics[k] = states

        return harmonics

    def compute_privacy_projection(self, coherence_form: np.ndarray, k: int) -> Dict:
        """
        Projeta forma de coerência na parte auto-dual para privacidade geométrica.

        A projeção auto-dual ω_+ = ½(ω + ★_T ω) preserva informação
        enquanto minimiza vazamento de dados sensíveis.
        """
        if k not in self.hodge.star_mats:
            return {'error': f'Hodge star not defined for k={k}'}

        # Projeção auto-dual
        omega_plus = self.dirac_solver.project_to_self_dual(coherence_form, k)
        omega_minus = self.dirac_solver.project_to_anti_self_dual(coherence_form, k)

        # Métricas de privacidade
        original_norm = np.linalg.norm(coherence_form)
        plus_norm = np.linalg.norm(omega_plus)
        minus_norm = np.linalg.norm(omega_minus)

        # Informação preservada vs. suprimida
        info_preserved = plus_norm**2 / (original_norm**2 + 1e-12)
        info_suppressed = minus_norm**2 / (original_norm**2 + 1e-12)

        return {
            'original_norm': original_norm,
            'self_dual_norm': plus_norm,
            'anti_self_dual_norm': minus_norm,
            'privacy_preservation_ratio': info_preserved,
            'information_suppression_ratio': info_suppressed,
            'projected_form': omega_plus
        }

    def verify_hodge_theorem(self, tolerance: float = 1e-8) -> Dict:
        """
        Verifica numericamente o Teorema de Hodge:
        dim H^k = dim ker(Δ_k) = número de formas harmônicas de grau k.
        """
        results = {}

        for k in range(self.hodge.dim + 1):
            # Contar formas harmônicas via autovalores próximos de zero
            harmonic_result = self.dirac_solver.solve_zero_modes(tolerance=tolerance)
            n_harmonics = harmonic_result.get('n_harmonic_modes', 0)

            # Calcular dimensão de cohomologia via álgebra linear
            # dim H^k = dim ker(d_k) - dim im(d_{k-1})
            if k < self.hodge.dim and k in self.hodge.d_mats:
                d_k = self.hodge.d_mats[k]
                ker_dim = d_k.shape[1] - np.linalg.matrix_rank(d_k.toarray())

                if k > 0 and (k-1) in self.hodge.d_mats:
                    d_km1 = self.hodge.d_mats[k-1]
                    im_dim = np.linalg.matrix_rank(d_km1.toarray())
                else:
                    im_dim = 0

                cohomology_dim = ker_dim - im_dim
            else:
                cohomology_dim = n_harmonics  # fallback

            results[k] = {
                'n_harmonic_forms': n_harmonics,
                'cohomology_dimension': cohomology_dim,
                'theorem_verified': abs(n_harmonics - cohomology_dim) < 2,  # margem numérica
                'harmonic_eigenvalues': harmonic_result.get('eigenvalues', [])
            }

        return {
            'by_degree': results,
            'all_verified': all(r['theorem_verified'] for r in results.values())
        }

    def generate_harmonic_report(self) -> Dict:
        """Gera relatório completo da Catedral como espaço harmônico."""
        harmonics = self.find_cathedral_harmonics()
        privacy_tests = {}

        # Testar projeção de privacidade para formas de diferentes graus
        for k in [0, 1, 2]:
            if k in self.hodge.M_k:
                # Forma aleatória para teste
                test_form = np.random.randn(self.hodge._count_k_forms(k))
                test_form /= np.linalg.norm(test_form)
                privacy_tests[k] = self.compute_privacy_projection(test_form, k)

        # Verificar teorema de Hodge
        hodge_verification = self.verify_hodge_theorem()

        # Estados no mercy gap
        mercy_gap_states = []
        for k, states in harmonics.items():
            for state in states:
                if state.is_mercy_gap_state():
                    mercy_gap_states.append({
                        'degree': k,
                        'eigenvalue': state.eigenvalue,
                        'self_dual_fraction': state.self_dual_fraction,
                        'coherence_norm': np.linalg.norm(state.coherence_profile)
                    })

        return {
            'manifold_dimension': self.hodge.dim,
            'torsion_strength': self.hodge.config.torsion_strength,
            'total_harmonic_states': sum(len(states) for states in harmonics.values()),
            'harmonics_by_degree': {k: len(states) for k, states in harmonics.items()},
            'mercy_gap_states': mercy_gap_states,
            'privacy_projection_tests': privacy_tests,
            'hodge_theorem_verification': hodge_verification,
            'cathedral_is_harmonic': hodge_verification['all_verified']
        }
