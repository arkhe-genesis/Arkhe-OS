import hashlib
import time
import random
from typing import Dict, List, Any

class InterSpeciesNodeConfig:
    def __init__(self, node_id: str, species_type: str, hardware_profile: Dict[str, Any]):
        self.node_id = node_id
        self.species_type = species_type
        self.hardware_profile = hardware_profile
        self.phi_c_reputation = 0.94 + random.uniform(0, 0.05)

    def measure_local_phi(self) -> float:
        # Mock calculation considering species diversity
        species_multiplier = {
            "Human": 1.0,
            "AI_Model": 0.9,
            "Cetacean_Sim": 0.85,
            "Avian_Sim": 0.75,
            "Mycelial_Network": 0.8
        }.get(self.species_type, 0.5)

        phi_local = (0.5 * random.random() + 0.5) * species_multiplier
        return max(0.0, min(0.9999, phi_local))

class CrossSpeciesExpander:
    def __init__(self):
        self.nodes = []

    def expand_nodes(self, target_count: int = 50) -> List[InterSpeciesNodeConfig]:
        """Expande para 50+ nós com diversidade inter-espécies."""
        species_distribution = {
            "Human": 0.4,
            "AI_Model": 0.3,
            "Cetacean_Sim": 0.1,
            "Avian_Sim": 0.1,
            "Mycelial_Network": 0.1
        }

        for i in range(target_count):
            species = random.choices(
                list(species_distribution.keys()),
                weights=list(species_distribution.values())
            )[0]

            hardware = {
                "cpu_cores": random.choice([4, 8, 16]),
                "ram_gb": random.choice([8, 16, 32]),
                "bandwidth_gbps": random.choice([1, 2.5, 10])
            }

            node_id = hashlib.sha3_256(f"species_node_{i}_{time.time()}".encode()).hexdigest()[:16]
            self.nodes.append(InterSpeciesNodeConfig(node_id, species, hardware))

        return self.nodes

    def calculate_collective_phi(self) -> float:
        if not self.nodes:
            return 0.0

        weighted_sum = sum(node.measure_local_phi() * node.phi_c_reputation for node in self.nodes)
        total_weight = sum(node.phi_c_reputation for node in self.nodes)

        return weighted_sum / max(1, total_weight)

if __name__ == "__main__":
    expander = CrossSpeciesExpander()
    nodes = expander.expand_nodes(55)
    print(f"Expanded to {len(nodes)} nodes with inter-species diversity.")

    species_count = {}
    for n in nodes:
        species_count[n.species_type] = species_count.get(n.species_type, 0) + 1

    for species, count in species_count.items():
        print(f" - {species}: {count}")

    print(f"Collective Phi_C: {expander.calculate_collective_phi():.4f}")
