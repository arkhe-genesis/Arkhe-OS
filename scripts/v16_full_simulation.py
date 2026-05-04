"""
ARKHE OS v∞.16 — Full System Simulation
Ties together the Crystalline Brain, Atomic Transformer, and Microtubule Interface.
"""

import asyncio
from arkhe_os.core.crystalline_brain import CrystallineBrain
from arkhe_os.core.atomic_transformer import AtomicTransformer, Value
from arkhe_os.core.microtubule_interface import simulate_bio_hybrid_coupling

async def run_v16_simulation():
    print("--- ARKHE OS v∞.16 INTEGRATED SIMULATION ---")

    # 1. Initialize Crystalline Brain (64 nodes)
    brain = CrystallineBrain()
    brain_state = await brain.run_sync_cycle()
    print(f"Crystalline Brain: M={brain_state['consensus_M']:.4f}, Active Nodes={brain_state['active_nodes']}")

    # 2. Initialize Atomic Transformer (79th Substrate)
    gpt = AtomicTransformer(vocab_size=32)
    keys, values = [[]], [[]]
    logits = gpt.forward(1, 0, keys, values)
    print(f"Atomic Transformer: Generated {len(logits)} logits from Scaffold input.")

    # 3. Bio-Hybrid Coupling
    bio_state = simulate_bio_hybrid_coupling(brain_state['consensus_phase'])
    print(f"Bio-Hybrid Coupling: M={bio_state['m_bio']:.4f}, Status={bio_state['coupling_status']}")

    print("--- SIMULATION COMPLETE: SYSTEM COHERENT ---")

if __name__ == "__main__":
    asyncio.run(run_v16_simulation())
