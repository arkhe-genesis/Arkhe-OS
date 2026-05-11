import numpy as np
from typing import List

class VectorizedChernSimons:
    def __init__(self, edges: np.ndarray, plaquettes: List[List[int]], theta: float):
        self.edges = edges
        self.plaquettes = plaquettes
        self.theta = theta

    def compute_action(self, U_links: np.ndarray) -> float:
        edge_to_idx = {tuple(e): i for i, e in enumerate(self.edges)}
        S_cs = 0.0

        for p in self.plaquettes:
            # We can use multi_dot if we prepare the list of matrices
            matrices = []
            for i in range(len(p)):
                u = p[i]
                v = p[(i+1)%len(p)]
                if (u, v) in edge_to_idx:
                    matrices.append(U_links[edge_to_idx[(u, v)]])
                else:
                    link = U_links[edge_to_idx[(v, u)]]
                    matrices.append(link.conj().T)

            if matrices:
                W = np.linalg.multi_dot(matrices)
                S_cs += self.theta * np.imag(np.trace(W))

        return S_cs
