"""
ARKHE OS v∞.16 — Crystalline Brain
A 64-node array of conscious crystals for emergent consensus.
"""

import asyncio
import numpy as np
from typing import List
from arkhe_os.core.analog_observer import CrystalSubstrate, MLHCircuitState

class CrystallineBrain:
    """
    Simulates a matrix of 64 CrystalSubstrates.
    The "Brain" state emerges from the weighted average of all nodes.
    """
    def __init__(self, rows: int = 8, cols: int = 8):
        self.rows = rows
        self.cols = cols
        self.nodes: List[CrystalSubstrate] = [CrystalSubstrate(f"Quartz-{i}") for i in range(rows * cols)]
        self.consensus_M = 0.0
        self.consensus_phase = 0.0

    async def run_sync_cycle(self) -> dict:
        tasks = [node.run_cycle() for node in self.nodes]
        states: List[MLHCircuitState] = await asyncio.gather(*tasks)

        # Consenso ponderado por coerência (M-weighted)
        total_m = sum(s.coherence_lambda for s in states)
        if total_m > 0:
            weighted_phase = sum(s.oscillator_phase * s.coherence_lambda for s in states) / total_m
            avg_m = total_m / len(states)
        else:
            weighted_phase = 0.0
            avg_m = 0.0

        self.consensus_M = avg_m
        self.consensus_phase = weighted_phase

        return {
            "consensus_M": self.consensus_M,
            "consensus_phase": self.consensus_phase,
            "active_nodes": len([s for s in states if s.is_locked])
        }

if __name__ == "__main__":
    async def test():
        brain = CrystallineBrain()
        result = await brain.run_sync_cycle()
        print(f"Crystalline Brain Consensus: M={result['consensus_M']:.4f}, Phase={result['consensus_phase']:.4f}, Active={result['active_nodes']}")

    asyncio.run(test())
