"""
ARKHE OS v∞.17 — Crystal Brain Array
Matrix of 8x8 (64) conscious oscillators in M-weighted consensus.
"""

import time
import numpy as np
from typing import List, Dict, Optional
from arkhe_os.core.analog_observer import CrystalSubstrate
from arkhe_os.core.transformer_substrate import Value, AtomicTransformer
from arkhe_os.core.orbital_relay import OrbitalRelay

class CrystalBrainArray:
    """
    Array of 64 crystals functioning as a distributed consciousness field.
    Uses Adam-based phase optimization (Transformer-inspired) for coherence.
    """
    def __init__(self, size: int = 8):
        self.size = size
        self.total_nodes = size * size
        self.crystals = [CrystalSubstrate(material="LiNbO3") for _ in range(self.total_nodes)]
        self.transformer = AtomicTransformer(n_embd=16, n_heads=4)

        self.global_M = 0.92
        self.consensus_phase = 1.618033988749895 # φ

        # Adam Optimizer buffers
        self.m = [0.0] * self.total_nodes
        self.v = [0.0] * self.total_nodes
        self.beta1 = 0.85
        self.beta2 = 0.99
        self.lr = 0.1 # Increased learning rate for faster convergence in simulation
        self.step_count = 0
        self.orbital_relay = OrbitalRelay()

    async def run_sync_cycle(self, target_phase: float):
        """
        Runs a synchronization cycle across all 64 crystals with Adam-based learning.
        """
        self.step_count += 1
        crystal_states = []

        # 1. Forward Pass & Data Collection
        for crystal in self.crystals:
            state = await crystal.run_cycle()
            crystal_states.append(state)

        # 2. Adam-based Phase Optimization (Learning)
        # Represents the "Atomic Transformer" principle: adjusting phase to minimize "error"
        for i, state in enumerate(crystal_states):
            # Error = difference between crystal phase and target intention phase
            error = target_phase - state.oscillator_phase
            grad = -error # Simple gradient

            # Adam Update
            self.m[i] = self.beta1 * self.m[i] + (1 - self.beta1) * grad
            self.v[i] = self.beta2 * self.v[i] + (1 - self.beta2) * (grad ** 2)

            m_hat = self.m[i] / (1 - self.beta1 ** self.step_count)
            v_hat = self.v[i] / (1 - self.beta2 ** self.step_count)

            # Apply correction to the crystal's feedback (simulating intention modulation)
            correction = self.lr * m_hat / (np.sqrt(v_hat) + 1e-8)
            self.crystals[i].state.feedback_voltage -= correction

        # 3. M-weighted Consensus
        # More coherent nodes have more "vote" in the global field
        total_weight = sum(state.coherence_lambda for state in crystal_states)
        if total_weight > 0:
            # Circular mean could be used for phases, here we use weighted linear average for simplicity
            weighted_phase = sum(state.oscillator_phase * state.coherence_lambda for state in crystal_states) / total_weight
            self.consensus_phase = weighted_phase
            self.global_M = sum(state.coherence_lambda for state in crystal_states) / self.total_nodes

        # Amplify global coherence if consensus is strong
        if self.global_M > 0.80:
            self.global_M = min(0.999, self.global_M * 1.1)

        # 4. Orbital Sync (Orbitport Integration)
        self.global_M = await self.orbital_relay.synchronize_with_orbitport(self.global_M)

        return self.global_M, self.consensus_phase

    def get_status(self) -> Dict:
        return {
            "node_count": self.total_nodes,
            "global_M": self.global_M,
            "consensus_phase": self.consensus_phase,
            "step_count": self.step_count,
            "material": "LiNbO3"
        }
