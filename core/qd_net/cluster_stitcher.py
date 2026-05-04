# core/qd_net/cluster_stitcher.py
"""
ARKHE QD-NET: Cluster State Stitcher
Implements the sequential emission + fusion protocol (Prasad et al.)
Target: 6-Ring Cluster State topology.
"""
import numpy as np
from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class ClusterNode:
    qubit_id: int
    position: np.ndarray  # 3D position in hex grid
    fidelity: float       # From Compute Shader
    entanglement_links: List[int] = None  # Connected qubit IDs

    def __post_init__(self):
        if self.entanglement_links is None:
            self.entanglement_links = []

class ClusterStitcher:
    def __init__(self, fusion_probability: float = 0.9, noise_strength: float = 0.0):
        self.p_fusion = fusion_probability
        self.noise = noise_strength
        self.graph_nodes = []
        self.graph_edges = []

    def step_fusion(self, photon_index: int, photon_fidelity: float) -> bool:
        """
        Attempts to fuse the new photon with the previous chain.
        Returns True if fusion succeeds (edge created), False otherwise.
        """
        # Noise degrades effective fusion probability
        effective_prob = self.p_fusion * (1.0 - self.noise)
        success = np.random.random() < effective_prob

        if success and photon_index > 0:
            # Create edge between current photon and previous one
            prev_id = photon_index - 1
            curr_id = photon_index

            self.graph_edges.append((prev_id, curr_id, photon_fidelity))

            # Update node data
            if len(self.graph_nodes) <= curr_id:
                self.graph_nodes.append(ClusterNode(qubit_id=curr_id, position=self._hex_position(curr_id), fidelity=photon_fidelity))
            else:
                self.graph_nodes[curr_id].fidelity = photon_fidelity
                self.graph_nodes[curr_id].entanglement_links.append(prev_id)

            if len(self.graph_nodes) <= prev_id:
                self.graph_nodes[prev_id].entanglement_links.append(curr_id)
            else:
                if prev_id not in self.graph_nodes[prev_id].entanglement_links:
                     self.graph_nodes[prev_id].entanglement_links.append(curr_id)

            return True
        else:
            # Fusion failed: Chain breaks or requires error correction (simulated as new node)
            if len(self.graph_nodes) <= photon_index:
                self.graph_nodes.append(ClusterNode(qubit_id=photon_index, position=self._hex_position(photon_index), fidelity=photon_fidelity * 0.5))
            return False

    def _hex_position(self, index: int) -> np.ndarray:
        """Maps linear index to hexagonal 6-ring topology."""
        if index == 0: return np.array([0, 0, 0]) # Center

        # Simple 6-ring logic: 1st ring 6 nodes, 2nd ring 12 nodes, etc.
        ring = 0
        count = 1
        while count + 6 * ring < index:
            count += 6 * ring
            ring += 1

        pos_in_ring = index - count
        angle = 2 * np.pi * pos_in_ring / (6 * ring) if ring > 0 else 0
        radius = ring * 1.5 # Spacing

        x = radius * np.cos(angle)
        y = radius * np.sin(angle)
        z = 0.0 # Planar cluster for now

        return np.array([x, y, z])

    def get_graph_data(self) -> Tuple[List[ClusterNode], List[Tuple]]:
        return self.graph_nodes, self.graph_edges