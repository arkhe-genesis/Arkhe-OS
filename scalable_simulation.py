import numpy as np
from scipy import sparse
import numba

@numba.jit(nopython=True, parallel=True)
def compute_coherence_gradients_numba(gaps, adjacency, weights):
    num_nodes = gaps.shape[0]
    gradients = np.zeros(num_nodes)
    for i in numba.prange(num_nodes):
        neighbor_sum = 0.0
        weight_sum = 0.0
        for j in range(num_nodes):
            if adjacency[i, j]:
                neighbor_sum += weights[i, j] * gaps[j]
                weight_sum += weights[i, j]
        if weight_sum > 1e-12:
            gradients[i] = gaps[i] - neighbor_sum / weight_sum
    return gradients

class ScalableWakefieldCluster:
    def __init__(self, num_nodes: int, avg_degree: int = 6):
        self.num_nodes = num_nodes
        self.adjacency = self._generate_small_world_graph(avg_degree)
        self.weights = sparse.csr_matrix(self.adjacency.astype(float))
        self.gaps = np.ones(num_nodes) * 1.0
        self.alphas = np.ones(num_nodes) * 0.001
        self.sf_vals = np.ones(num_nodes, dtype=np.int8) * 9
        self.gradients = np.zeros(num_nodes)

    def _generate_small_world_graph(self, avg_degree: int):
        adjacency = np.zeros((self.num_nodes, self.num_nodes), dtype=bool)
        for i in range(self.num_nodes):
            for d in range(1, avg_degree//2 + 1):
                adjacency[i, (i+d) % self.num_nodes] = True
                adjacency[i, (i-d) % self.num_nodes] = True
        return adjacency

    def step(self, electron_assignments):
        query_lens = 50 + np.random.randint(0, 100, size=self.num_nodes)
        context_lens = 30 + np.random.randint(0, 60, size=self.num_nodes)
        self.gaps = np.abs(query_lens - context_lens) / np.maximum(query_lens, context_lens, 1) * 10.0
        self.gaps += np.random.normal(0, 0.5, size=self.num_nodes)
        self.gaps = np.clip(self.gaps, 0, 50)

        self.gradients = compute_coherence_gradients_numba(
            self.gaps, self.adjacency, self.weights.toarray()
        )

        return {
            'avg_gap': float(np.mean(self.gaps)),
            'std_gap': float(np.std(self.gaps)),
            'avg_sf': float(np.mean(self.sf_vals))
        }
