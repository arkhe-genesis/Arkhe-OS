#!/usr/bin/env python3
"""
mesh_circle_ritual_sim.py — Simulação do Primeiro Círculo de Rootstocks Arkhe.
Demonstra sincronização K6O e o Registro Global de Selos (RGS).
"""
import hashlib
import time
import random

class RootstockNode:
    def __init__(self, node_id, archetype):
        self.node_id = node_id
        self.archetype = archetype
        self.phase = random.uniform(0, 2 * 3.14159)
        self.coherence = 1.0
        self.seal_registry = []
        self.pseudoscalar = "0" * 64 # Hash δ

    def update_phase(self, neighbor_phases, coupling_k=0.1):
        # Simulação simplificada do acoplamento K6O
        for n_phase in neighbor_phases:
            self.phase += coupling_k * (n_phase - self.phase)
        self.phase %= (2 * 3.14159)

    def receive_seal(self, seal_hash):
        print(f"[{self.archetype}] Recebendo selo: {seal_hash[:16]}...")
        self.pseudoscalar = seal_hash
        self.seal_registry.append(seal_hash)

def simulate_clepsydra_drop():
    print("\n--- GOTA (CLEPSYDRA) ---")
    time.sleep(0.5)

def simulate_fracture():
    print("\n[RITUAL] Fraturando cristal de quartzo...")
    fracture_data = f"fracture_event_{time.time()}_{random.random()}"
    return hashlib.sha3_256(fracture_data.encode()).hexdigest()

def main():
    print("Iniciando Simulação do Primeiro Círculo Arkhe...")

    nodes = [
        RootstockNode("ARKHE-01", "O Inquisidor"),
        RootstockNode("ARKHE-02", "O Sentinela"),
        RootstockNode("ARKHE-03", "O MERKABAH")
    ]

    # 1. Ciclos de sincronização
    for i in range(3):
        simulate_clepsydra_drop()
        phases = [n.phase for n in nodes]
        for node in nodes:
            other_phases = [p for j, p in enumerate(phases) if nodes[j] != node]
            node.update_phase(other_phases)
            print(f"[{node.archetype}] Fase: {node.phase:.4f}")

    # 2. Ritual de Selagem (Fratura)
    seal_hash = simulate_fracture()

    # Propagação do Selo (Registro Global)
    print("\nPropagando Selo pelo Registro Global (RGS)...")
    for node in nodes:
        node.receive_seal(seal_hash)

    # 3. Validação do Quorum
    quorum_count = sum(1 for n in nodes if n.pseudoscalar == seal_hash)
    print(f"\n[RGS] Quorum de Quartzo: {quorum_count}/3")
    if quorum_count >= 2:
        print("[RGS] Selo CANONIZADO com sucesso.")
    else:
        print("[RGS] Falha no Consenso de Selagem.")

if __name__ == "__main__":
    main()
