import math
from typing import Dict, List, Optional, Set, Tuple
from core.multi_modal.orthogonal_witness import MultiModalPhaseAlignedStateVector

class MetaLatticeExpansion:
    """
    Maps orthogonal witness states (triads) into a cross-participant lattice.
    Expands the single-node / single-triad orthogonal witness into a robust,
    coherent meta-lattice where multiple triads share edges (participants).
    """

    def __init__(self):
        # A ledger of known triads. Key: sorted tuple of 3 participant IDs
        self.triads: Dict[Tuple[str, str, str], 'TriadWitness'] = {}
        # Adjacency map. Key: Participant ID, Value: Set of connected Participant IDs
        self.lattice_graph: Dict[str, Set[str]] = {}

    def register_triad(self, participants: Tuple[str, str, str], witness_state: MultiModalPhaseAlignedStateVector):
        """Registers a new orthogonal witness triad into the meta-lattice."""
        sorted_p = tuple(sorted(participants))
        self.triads[sorted_p] = TriadWitness(participants=sorted_p, witness_state=witness_state)

        # Update lattice graph with edges from this triad
        for i in range(3):
            for j in range(i + 1, 3):
                p1 = sorted_p[i]
                p2 = sorted_p[j]
                if p1 not in self.lattice_graph:
                    self.lattice_graph[p1] = set()
                if p2 not in self.lattice_graph:
                    self.lattice_graph[p2] = set()
                self.lattice_graph[p1].add(p2)
                self.lattice_graph[p2].add(p1)

    def map_witness_to_lattice(self) -> Dict[str, List[str]]:
        """
        Maps the current triads into a coherent meta-lattice structure.
        Returns the lattice view as a dictionary of participant to their multi-triad neighbors.
        """
        lattice_view = {}
        for participant, neighbors in self.lattice_graph.items():
            lattice_view[participant] = list(neighbors)

        return lattice_view

    def compute_lattice_coherence(self) -> float:
        """
        Computes the global coherence of the meta-lattice by averaging the
        multi-modal PDI of all registered triads.
        """
        if not self.triads:
            return 0.0

        total_pdi = sum(triad.witness_state.pdi_multi for triad in self.triads.values())
        return total_pdi / len(self.triads)

    def find_shared_edges(self) -> List[Tuple[str, str]]:
        """
        Identifies edges (participant pairs) that are shared across multiple triads.
        These shared edges represent the 'glue' of the meta-lattice expansion.
        """
        edge_counts = {}

        for triad_nodes in self.triads.keys():
            # Extract the 3 edges of the triad
            edges = [
                tuple(sorted([triad_nodes[0], triad_nodes[1]])),
                tuple(sorted([triad_nodes[1], triad_nodes[2]])),
                tuple(sorted([triad_nodes[0], triad_nodes[2]]))
            ]

            for edge in edges:
                if edge not in edge_counts:
                    edge_counts[edge] = 0
                edge_counts[edge] += 1

        # Return edges that belong to more than one triad
        return [edge for edge, count in edge_counts.items() if count > 1]


class TriadWitness:
    """Represents a coherent state built from an orthogonal witness shared by three participants."""
    def __init__(self, participants: Tuple[str, str, str], witness_state: MultiModalPhaseAlignedStateVector):
        self.participants = participants
        self.witness_state = witness_state
