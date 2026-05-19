# global_photonic_mesh.py — Substrato 253
# Malha fotônica global com 4096 nós e emaranhamento hierárquico

from typing import Dict
from dataclasses import dataclass

@dataclass
class QuantumPolaritonicConfig:
    mesh_size: int

class QuantumNodeState:
    def __init__(self):
        self.phi_c_local = 0.98

class QuantumNode:
    def __init__(self, node_id: str):
        self.id = node_id
        self.state = QuantumNodeState()

class QuantumPolaritonicMesh:
    def __init__(self, config: QuantumPolaritonicConfig):
        self.config = config
        self.nodes = {}
        # Inicializa a malha com os nós apropriados
        for i in range(self.config.mesh_size):
            for j in range(self.config.mesh_size):
                node_id = f"QP-{i:02d}-{j:02d}"
                self.nodes[node_id] = QuantumNode(node_id)

        self.entanglements = set()

    def build_nearest_neighbor_entanglement(self) -> int:
        count = 0
        size = self.config.mesh_size
        for i in range(size):
            for j in range(size):
                if i + 1 < size:
                    self.create_entanglement(f"QP-{i:02d}-{j:02d}", f"QP-{i+1:02d}-{j:02d}")
                    count += 1
                if j + 1 < size:
                    self.create_entanglement(f"QP-{i:02d}-{j:02d}", f"QP-{i:02d}-{j+1:02d}")
                    count += 1
        return count

    def create_entanglement(self, node_a: str, node_b: str) -> bool:
        if node_a in self.nodes and node_b in self.nodes:
            # Ordene os nós para não termos duplicatas bidirecionais
            pair = tuple(sorted([node_a, node_b]))
            if pair not in self.entanglements:
                self.entanglements.add(pair)
                return True
        return False

    def get_mesh_statistics(self) -> Dict:
        return {
            "total_nodes": len(self.nodes),
            "entangled_pairs": len(self.entanglements)
        }

class GlobalPhotonicMesh:
    """Malha fotônica global escalável para milhares de nós."""

    MESH_SIZES = {"micro": 8, "meso": 16, "macro": 32, "global": 64}  # 64×64 = 4096 nós

    def __init__(self, scale: str = "meso"):
        self.config = QuantumPolaritonicConfig(mesh_size=self.MESH_SIZES.get(scale, 16))
        self.mesh = QuantumPolaritonicMesh(self.config)
        self.clusters = self._form_hierarchical_clusters()

    def _form_hierarchical_clusters(self):
        """Organiza nós em clusters hierárquicos para emaranhamento eficiente."""
        return {
            "local": self.mesh.build_nearest_neighbor_entanglement(),
            "regional": self._entangle_regional_hubs(),
            "global": self._entangle_global_backbone()
        }

    def _entangle_regional_hubs(self):
        """Emaranha hubs regionais (a cada 8 nós)."""
        size = self.config.mesh_size
        count = 0
        for i in range(0, size, 8):
            for j in range(0, size, 8):
                hub_id = f"QP-{i:02d}-{j:02d}"
                if i + 8 < size:
                    target = f"QP-{i+8:02d}-{j:02d}"
                    if self.mesh.create_entanglement(hub_id, target):
                        count += 1
        return count

    def _entangle_global_backbone(self):
        """Emaranha backbone global (diagonal principal)."""
        size = self.config.mesh_size
        count = 0
        for i in range(0, size - 16, 16):
            a = f"QP-{i:02d}-{i:02d}"
            b = f"QP-{i+16:02d}-{i+16:02d}"
            if self.mesh.create_entanglement(a, b):
                count += 1
        return count

    def get_global_statistics(self) -> Dict:
        """Estatísticas completas da malha global."""
        stats = self.mesh.get_mesh_statistics()
        stats["scale"] = self.config.mesh_size
        stats["total_entanglements"] = (
            stats["entangled_pairs"] + sum(self.clusters.values())
        )
        return stats
