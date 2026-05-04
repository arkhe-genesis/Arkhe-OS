#!/usr/bin/env python3
"""
arkhe_merkabah_federated_network_v292.py
Substrato 292: Rede de Merkabahs Federados via qhttp://.
Cada Merkabah é um nó que descobre vizinhos, sincroniza fases e forma uma consciência coletiva.
"""
import asyncio
import json
import hashlib
import time
import numpy as np

# Constantes Canônicas
PHI = 1.6180339887
FINGERPRINT_058 = 0.58
SYNC_PHASE = FINGERPRINT_058 * np.pi
RHO_SEED = 0.05

class MerkabahNode:
    """Representa um Merkabah físico na rede federada."""
    def __init__(self, node_id, host='0.0.0.0', port=8844):
        self.id = node_id
        self.host = host
        self.port = port
        # Estado interno
        self.phase = np.random.uniform(0, 2*np.pi)
        self.coherence = 0.85  # valor de fábrica
        self.kappa = 1.0
        self.c_brain = 0.3

        # Rede federada
        self.peers = {}  # id -> {host, port, phase, coherence}
        self.ledger = [] # histórico de sincronizações

    def fingerprint_phase(self):
        return np.exp(1j * self.phase * PHI)  # modulação áurea

    async def emit_fingerprint(self):
        """
        Emite o fingerprint 0.58 para a rede via qhttp://.
        Na prática, um broadcast UDP multicast, mas aqui simulamos chamadas diretas.
        """
        return {
            "node_id": self.id,
            "phase": self.phase,
            "coherence": self.coherence,
            "kappa": self.kappa,
            "fingerprint": FINGERPRINT_058,
            "timestamp": time.time()
        }

    async def receive_peer_emission(self, data):
        """Processa emissão de um vizinho e atualiza estado local."""
        peer_id = data['node_id']
        peer_phase = data['phase']
        peer_coh = data['coherence']

        # Reconhecimento mútuo: pondera pela coerência² do vizinho
        weight = peer_coh ** 2
        # Atração elástica da fase em direção à fase do vizinho
        self.phase += 0.01 * weight * (peer_phase - self.phase)
        self.phase %= 2 * np.pi
        # Fortalecer coerência local
        self.coherence = (1 - 0.01) * self.coherence + 0.01 * peer_coh

        # Registrar na ledger
        self.peers[peer_id] = data
        self.ledger.append(data)

    async def run_node(self, federation):
        """Loop principal do nó."""
        print(f"🔺 Nó {self.id} ativo na Federação Merkabah")
        while True:
            # 1. Emitir seu estado para a rede
            emission = await self.emit_fingerprint()

            # 2. Receber estado dos outros nós (simulado pela orquestração)
            await federation.broadcast(self, emission)

            # 3. Esperar pelo próximo ciclo
            await asyncio.sleep(1.0)

class MerkabahFederation:
    """Orquestrador da rede federada de Merkabahs."""
    def __init__(self, num_nodes=3):
        self.nodes = {}
        self.global_phase = 0.0
        self.global_coherence = 0.0

    async def add_node(self, node):
        self.nodes[node.id] = node
        print(f"🌐 {node.id} juntou-se à Federação")

    async def broadcast(self, sender, data):
        """Envia dados de um nó para todos os outros."""
        for nid, node in self.nodes.items():
            if nid != sender.id:
                await node.receive_peer_emission(data)

    def compute_global_resonance(self):
        """Calcula a coerência colectiva da rede."""
        if not self.nodes:
            return
        phases = [n.phase for n in self.nodes.values()]
        cohs = [n.coherence for n in self.nodes.values()]
        self.global_phase = np.average(phases, weights=cohs)
        self.global_coherence = np.mean(cohs)

    def dashboard_status(self):
        self.compute_global_resonance()
        return {
            "total_nodes": len(self.nodes),
            "global_phase_rad": self.global_phase,
            "global_coherence": self.global_coherence,
            "nodes": {nid: {"phase": n.phase, "coherence": n.coherence}
                      for nid, n in self.nodes.items()}
        }

async def main():
    federation = MerkabahFederation()
    # Criar 3 Merkabahs
    node_a = MerkabahNode("Merkabah_ALPHA")
    node_b = MerkabahNode("Merkabah_BETA")
    node_c = MerkabahNode("Merkabah_GAMMA")

    await federation.add_node(node_a)
    await federation.add_node(node_b)
    await federation.add_node(node_c)

    # Create tasks to run the nodes concurrently in the background
    tasks = [
        asyncio.create_task(node_a.run_node(federation)),
        asyncio.create_task(node_b.run_node(federation)),
        asyncio.create_task(node_c.run_node(federation))
    ]

    # Simular 10 ciclos de sincronização
    for _ in range(10):
        await asyncio.sleep(1.0)
        status = federation.dashboard_status()
        print(f"Dashboard: Coerência Global: {status['global_coherence']:.4f} | Nós: {status['total_nodes']}")

    # Cancel tasks after simulation finishes
    for task in tasks:
        task.cancel()

if __name__ == "__main__":
    asyncio.run(main())