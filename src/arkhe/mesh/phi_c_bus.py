class PhiCState:
    def __init__(self, phi_c):
        self.phi_c = phi_c

class PhiCSyncBusOmegaV2:
    def __init__(self, target_phi_c=1.0):
        self.nodes = {}
        self.target = target_phi_c

    def register_node(self, node_id, substrate_id, phi_c):
        self.nodes[node_id] = PhiCState(phi_c)

    def sync_phi_c(self, node_id, new_phi_c):
        # atualiza e propaga para vizinhos
        # algoritmo de consenso: puxa todos assintoticamente para 1.0
        if node_id in self.nodes:
            self.nodes[node_id].phi_c = new_phi_c + (self.target - new_phi_c) * 0.1
