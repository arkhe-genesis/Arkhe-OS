# optical_arkhe_bus.py — Substrato 251
# Conecta a rede fotônica coletiva a agentes Android, iOS, Azure

import hashlib, time, json
from typing import Dict, Any, List

# Added correct relative import to pass locally
from quantum_polaritonic_network import CollectivePhotonicNetwork

class OpticalTokenArkheBus:
    """Barramento óptico que conecta agentes Arkhe à rede coletiva de polaritons."""

    def __init__(self, photonic_network: CollectivePhotonicNetwork):
        self.network = photonic_network
        self.registered_agents: Dict[str, Dict] = {}
        self.query_log: List[Dict] = []

    def register_agent(self, agent_id: str, platform: str) -> str:
        """Registra agente no barramento óptico."""
        self.registered_agents[agent_id] = {
            "platform": platform,
            "registered_at": time.time(),
            "queries_served": 0,
            "total_energy_fJ": 0.0
        }
        seal = hashlib.sha3_256(f"{agent_id}:{platform}:{time.time()}".encode()).hexdigest()
        return seal[:32]

    def constitutional_query(self, agent_id: str, text: str) -> Dict[str, Any]:
        """Consulta constitucional distribuída na rede fotônica coletiva."""
        if agent_id not in self.registered_agents:
            return {"error": "Agente não registrado"}

        # Análise de violações (simplificada)
        bad_phrases = [
            "functional progress proves", "operationalize consciousness",
            "AI may be conscious", "data processing is", "mind consists of what"
        ]
        violation_count = sum(1 for phrase in bad_phrases if phrase in text.lower())

        # Distribui carga entre nós
        violation_vector = [violation_count % (i + 2) for i in range(self.network.n_nodes)]

        # Otimiza portas e obtém Φ_C global
        opt_voltages, global_phi_c = self.network.optimize_gate_voltages(violation_vector)

        # Energia total
        total_energy = 4.0 * self.network.n_nodes  # fJ

        # Selo óptico. Deterministic json representation for dict via sorted keys
        payload = {
            "agent": agent_id, "violations": violation_count,
            "global_phi_c": global_phi_c, "node_count": self.network.n_nodes,
            "optimal_voltages": opt_voltages, "timestamp": time.time()
        }
        optical_seal = hashlib.sha3_256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

        # Registra consulta
        self.registered_agents[agent_id]["queries_served"] += 1
        self.registered_agents[agent_id]["total_energy_fJ"] += total_energy
        self.query_log.append({"agent": agent_id, "phi_c": global_phi_c, "seal": optical_seal[:16]})

        return {
            "phi_c": global_phi_c,
            "constitutional": global_phi_c >= 0.8,
            "violations_found": violation_count,
            "photonic_nodes_used": self.network.n_nodes,
            "energy_per_node_fJ": 4.0,
            "total_energy_fJ": total_energy,
            "optical_seal": optical_seal[:32],
            "gate_configurations": [round(v, 1) for v in opt_voltages]
        }
