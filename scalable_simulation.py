import numpy as np
from scipy import sparse
from collections import defaultdict
import numba  # @jit para aceleração

@numba.jit(nopython=True, parallel=True)
def compute_coherence_gradients_numba(
    gaps: np.ndarray,  # (num_nodes,)
    adjacency: np.ndarray,  # (num_nodes, num_nodes) boolean
    weights: np.ndarray  # (num_nodes, num_nodes) weights
) -> np.ndarray:
    """Computa gradientes de coerência com Numba para performance."""
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
    """Cluster escalável com sparse adjacency e atualização incremental."""

    def __init__(self, num_nodes: int, avg_degree: int = 6):
        self.num_nodes = num_nodes
        # Grafo sparse: cada nó conectado a ~avg_degree vizinhos
        self.adjacency = self._generate_small_world_graph(avg_degree)
        self.weights = sparse.csr_matrix(self.adjacency.astype(float))

        # Estado dos agentes (usar arrays para cache efficiency)
        self.gaps = np.ones(num_nodes) * 1.0  # gap inicial
        self.alphas = np.ones(num_nodes) * 0.001
        self.sf_vals = np.ones(num_nodes, dtype=np.int8) * 9  # SF inicial

        # Cache de gradientes (atualizado incrementalmente)
        self.gradients = np.zeros(num_nodes)
        self.last_gradient_update = 0

    def _generate_small_world_graph(self, avg_degree: int) -> np.ndarray:
        """Gera grafo small-world (Watts-Strogatz) para simular rede real."""
        # Cada nó conectado a avg_degree/2 vizinhos em cada direção + rewiring
        adjacency = np.zeros((self.num_nodes, self.num_nodes), dtype=bool)
        for i in range(self.num_nodes):
            for d in range(1, avg_degree//2 + 1):
                adjacency[i, (i+d) % self.num_nodes] = True
                adjacency[i, (i-d) % self.num_nodes] = True
        # Rewiring probabilístico (prob=0.1)
        for i in range(self.num_nodes):
            for j in range(self.num_nodes):
                if adjacency[i, j] and np.random.random() < 0.1:
                    adjacency[i, j] = False
                    # Reconectar a nó aleatório não-vizinho
                    candidates = [k for k in range(self.num_nodes)
                                if k != i and not adjacency[i, k]]
                    if candidates:
                        adjacency[i, np.random.choice(candidates)] = True
        return adjacency

    def update_agents_batch(self, query_lens: np.ndarray, context_lens: np.ndarray):
        """Atualiza gaps de todos os agentes em batch (vetorizado)."""
        # Vetorizado: muito mais rápido que loop Python
        self.gaps = np.abs(query_lens - context_lens) / np.maximum(query_lens, context_lens) * 10.0
        self.gaps += np.random.normal(0, 0.5, size=self.num_nodes)
        self.gaps = np.clip(self.gaps, 0, 50)

        # Meta-adaptação vetorial
        hallucinations = self.gaps > 15.0
        self.alphas[hallucinations] *= 0.99
        self.alphas[~hallucinations] = np.minimum(0.01, self.alphas[~hallucinations] * 1.0001)

    def compute_gradients_incremental(self, changed_nodes: np.ndarray):
        """Atualiza gradientes apenas para nós que mudaram (otimização)."""
        # Para grande escala: não recalcular todos os gradientes
        for i in changed_nodes:
            neighbor_sum = 0.0
            weight_sum = 0.0
            # Iterar apenas sobre vizinhos (sparse)
            for j in range(self.num_nodes):
                if self.adjacency[i, j]:
                    neighbor_sum += self.gaps[j]
                    weight_sum += 1.0
            if weight_sum > 1e-12:
                self.gradients[i] = self.gaps[i] - neighbor_sum / weight_sum

    def adapt_lora_parameters(self, priorities: np.ndarray, rssi_vals: np.ndarray):
        """Ajusta SF em batch baseado em gaps e prioridades."""
        # Vetorizado: ajustar todos os SFs de uma vez
        sf_offsets = np.clip(5 * self.gaps / 50.0, 0, 5).astype(int)
        self.sf_vals = np.clip(7 + sf_offsets, 7, 12).astype(np.int8)

        # Ajuste fino baseado em prioridade e RSSI (vetorizado)
        x = 0.8 * priorities - 0.3 * (rssi_vals + 100) / 100
        sigmoid = 1 / (1 + np.exp(-x))
        # TX power não afeta SF, mas pode ser usado para logging

    def step(self, electron_assignments: np.ndarray) -> dict:
        """Um passo da simulação escalável."""
        # 1. Atualizar agentes (batch)
        query_lens = 50 + np.random.randint(0, 100, size=self.num_nodes)
        context_lens = 30 + np.random.randint(0, 60, size=self.num_nodes)
        self.update_agents_batch(query_lens, context_lens)

        # 2. Calcular gradientes (incremental ou full)
        if np.random.random() < 0.1:  # Recalcular full a cada 10 passos
            self.gradients = compute_coherence_gradients_numba(
                self.gaps, self.adjacency, self.weights.toarray()
            )
        else:
            # Atualizar apenas nós com mudança significativa
            changed = np.abs(self.gaps - np.roll(self.gaps, 1)) > 0.5
            self.compute_gradients_incremental(np.where(changed)[0])

        # 3. Calcular prioridades para elétrons
        total_grad = np.sum(np.abs(self.gradients)) + 1e-6
        priorities = (np.abs(self.gradients) / total_grad) * np.exp(-self.gaps / 15.0)

        # 4. Acelerar elétrons (vetorizado)
        accelerations = np.maximum(0, 10.0 - self.gaps[electron_assignments]) * 0.3
        # (aplicar aceleração aos elétrons...)

        # 5. Adaptar parâmetros LoRa
        rssi_vals = -70 + np.random.normal(0, 10, size=self.num_nodes)
        self.adapt_lora_parameters(priorities, rssi_vals)

        return {
            'avg_gap': float(np.mean(self.gaps)),
            'std_gap': float(np.std(self.gaps)),
            'avg_sf': float(np.mean(self.sf_vals)),
            'num_hallucinations': int(np.sum(self.gaps > 15.0))
        }
