# core/qd_net/cluster_stitcher_fixed.py
"""
ARKHE QD-NET: Cluster State Stitcher — 6-Ring Topology Corrected
Implements sequential emission + fusion + explicit ring closure.
"""
import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass, field

@dataclass
class ClusterNode:
    qubit_id: int
    position: np.ndarray
    fidelity: float
    entanglement_links: List[int] = field(default_factory=list)

class ClusterStitcher:
    def __init__(self, n_target: int = 6, fusion_probability: float = 0.9, noise_strength: float = 0.0):
        self.n_target = n_target  # Target ring size
        self.p_fusion = fusion_probability * (1.0 - noise_strength)
        self.nodes: List[ClusterNode] = []
        self.edges: List[Tuple[int, int, float]] = []

    def build_6_ring(self, fidelities: List[float]) -> Tuple[List[ClusterNode], List[Tuple]]:
        """
        Constructs a 6-ring cluster state with explicit closure.
        fidelities: List of length n_target with per-photon fidelity values.
        """
        n = self.n_target
        if len(fidelities) < n:
            raise ValueError(f"Need at least {n} fidelities for {n}-ring")

        # Step 1: Create nodes with correct hexagonal positions
        for i in range(n):
            pos = self._hex_position_ring(i, n)
            self.nodes.append(ClusterNode(
                qubit_id=i,
                position=pos,
                fidelity=fidelities[i]
            ))

        # Step 2: Create edges via sequential fusion (linear chain first)
        for i in range(n - 1):
            if np.random.random() < self.p_fusion:
                self._add_edge(i, i + 1, min(fidelities[i], fidelities[i + 1]))

        # Step 3: EXPLICIT CLOSURE — Fuse last to first to complete ring
        if np.random.random() < self.p_fusion:
            self._add_edge(n - 1, 0, min(fidelities[n - 1], fidelities[0]))

        return self.nodes, self.edges

    def _add_edge(self, i: int, j: int, fidelity: float):
        """Adds bidirectional edge with fidelity weight."""
        self.edges.append((i, j, fidelity))
        if j not in self.nodes[i].entanglement_links:
            self.nodes[i].entanglement_links.append(j)
        if i not in self.nodes[j].entanglement_links:
            self.nodes[j].entanglement_links.append(i)

    def _hex_position_ring(self, index: int, ring_size: int) -> np.ndarray:
        """
        Positions nodes on a regular hexagon (2D planar ring).
        For ring_size=6: angles at 0°, 60°, 120°, 180°, 240°, 300°.
        """
        if ring_size <= 1:
            return np.array([0.0, 0.0, 0.0])

        radius = 2.0  # Fixed radius for visualization clarity
        angle = 2 * np.pi * index / ring_size
        x = radius * np.cos(angle)
        y = radius * np.sin(angle)
        return np.array([x, y, 0.0])

    def validate_topology(self) -> dict:
        """Validates that the result is a proper 6-ring."""
        if len(self.nodes) != self.n_target:
            return {"valid": False, "error": f"Wrong node count: {len(self.nodes)} vs {self.n_target}"}

        # Check each node has degree 2 (ring property)
        for node in self.nodes:
            if len(node.entanglement_links) != 2:
                return {
                    "valid": False,
                    "error": f"Node {node.qubit_id} has degree {len(node.entanglement_links)}, expected 2"
                }

        # Check edge count
        if len(self.edges) != self.n_target:
            return {"valid": False, "error": f"Wrong edge count: {len(self.edges)} vs {self.n_target}"}

        return {"valid": True, "nodes": len(self.nodes), "edges": len(self.edges)}