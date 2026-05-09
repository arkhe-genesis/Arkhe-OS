import numpy as np
from typing import Dict, Any, List

class ConnectomePolytopeAnalyzer:
    def __init__(self, connectivity_matrix: np.ndarray):
        self.W = connectivity_matrix
        self.n_regions = self.W.shape[0]
        degrees = np.sum(self.W, axis=1)
        self.L = np.diag(degrees) - self.W
    def compute_spectrum(self, k: int = 20) -> Dict[str, Any]:
        eigenvalues = np.linalg.eigvalsh(self.L)
        k_indices = np.arange(1, len(eigenvalues))
        log_k = np.log(k_indices)
        log_lambda = np.log(eigenvalues[1:] + 1e-10)
        coeffs = np.polyfit(log_k, log_lambda, 1)
        d_spectral = 2 / (coeffs[0] + 1e-6)
        return {
            'eigenvalues': eigenvalues[:k],
            'spectral_dimension': float(d_spectral),
            'degeneracy_count': int(np.sum(np.diff(eigenvalues[:k]) < 1e-4))
        }
    def map_states(self, coherence_data: Dict[str, float]) -> Dict[str, Any]:
        spectrum = self.compute_spectrum()
        evs = spectrum['eigenvalues']
        mapping = {}
        for state, l2 in coherence_data.items():
            idx = np.argmin(np.abs(evs - l2 * np.max(evs)))
            is_q = bool(np.abs(evs[idx] - l2 * np.max(evs)) < 0.1)
            mapping[state] = {
                'l2_observed': l2,
                'eigenvalue_assigned': float(evs[idx]),
                'is_quantized': is_q
            }
        return {
            'mapping': mapping,
            'all_quantized': bool(all(m['is_quantized'] for m in mapping.values())),
            'spectral_dim': spectrum['spectral_dimension']
        }
