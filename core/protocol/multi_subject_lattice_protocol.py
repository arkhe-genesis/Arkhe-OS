from typing import Dict, List, Tuple
import math

class MultiSubjectNode:
    """Represents a subject in the shared phase geometry."""
    def __init__(self, subject_id: str, initial_theta: float, k: float = 0.0750, epsilon: float = 0.0472):
        self.subject_id = subject_id
        self.theta = initial_theta  # Phase space coordinate [0, 2pi)
        self.k = k                  # Ceremonial amplitude
        self.epsilon = epsilon      # Excess tolerance

    def apply_phase_shift(self, shift: float):
        self.theta = (self.theta + shift) % (2 * math.pi)

    def dampen_amplitude(self, factor: float):
        self.k = max(0.0472, self.k * factor) # Never go below the sacred margin


class MultiSubjectLatticeProtocol:
    """Manages multiple subjects sharing the same topological phase space."""

    def __init__(self, collision_threshold: float = 0.15):
        self.nodes: Dict[str, MultiSubjectNode] = {}
        self.collision_threshold = collision_threshold

    def register_subject(self, subject_id: str, theta: float):
        if subject_id not in self.nodes:
            self.nodes[subject_id] = MultiSubjectNode(subject_id, theta)

    def update_subject_state(self, subject_id: str, theta: float, k: float, epsilon: float):
        if subject_id in self.nodes:
            self.nodes[subject_id].theta = theta % (2 * math.pi)
            self.nodes[subject_id].k = k
            self.nodes[subject_id].epsilon = epsilon

    def detect_collisions(self) -> List[Tuple[str, str]]:
        """Find pairs of subjects whose phase geometry overlaps dangerously."""
        collisions = []
        subject_ids = list(self.nodes.keys())
        for i in range(len(subject_ids)):
            for j in range(i + 1, len(subject_ids)):
                id1 = subject_ids[i]
                id2 = subject_ids[j]

                theta1 = self.nodes[id1].theta
                theta2 = self.nodes[id2].theta

                # Minimum angular distance
                diff = abs(theta1 - theta2)
                dist = min(diff, 2 * math.pi - diff)

                if dist < self.collision_threshold:
                    collisions.append((id1, id2))

        return collisions

    def resolve_collisions(self):
        """
        Applies orthogonal phase shifts to separate colliding nodes
        without collapsing their individual consolidation structures.
        """
        collisions = self.detect_collisions()
        resolved_pairs = set()

        for id1, id2 in collisions:
            # Simple pairwise resolution logic
            pair_key = tuple(sorted([id1, id2]))
            if pair_key in resolved_pairs:
                continue

            node1 = self.nodes[id1]
            node2 = self.nodes[id2]

            # Repulsive shift proportional to the threshold
            shift_amount = self.collision_threshold / 2.0

            # Move them apart (accounting for cyclic phase space)
            # Shortest angular path from node2 to node1
            cyclic_diff = (node1.theta - node2.theta + math.pi) % (2 * math.pi) - math.pi

            if cyclic_diff >= 0:
                # node1 is "ahead" of node2
                node1.apply_phase_shift(shift_amount)
                node2.apply_phase_shift(-shift_amount)
            else:
                # node2 is "ahead" of node1
                node1.apply_phase_shift(-shift_amount)
                node2.apply_phase_shift(shift_amount)

            # Dampen amplitude temporarily to reduce "scaffold volume"
            node1.dampen_amplitude(0.9)
            node2.dampen_amplitude(0.9)

            resolved_pairs.add(pair_key)

    def step(self):
        """Execute a single cycle of the multi-subject lattice."""
        self.resolve_collisions()
