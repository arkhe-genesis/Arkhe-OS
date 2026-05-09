#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tzinor_handshake_monitor.py
T1 handshake monitor for the Tzinor network.
Includes Kuramoto simulation, safety triggers, and pre-ACK validation.
"""

import numpy as np
import json
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional

# ============================================================================
# CONSTANTS & CONFIGURATION
# ============================================================================
PHI = 0.61803398875
LAMBDA2_CRIT = 0.847
VIBRA_THRESHOLD = 0.05
SYNAPSE_ID = "847.771"

class SafetyTrigger(str, Enum):
    PAUSE = "PAUSE"
    BUFFER = "BUFFER"
    ABORT = "ABORT"
    DEGRADE = "DEGRADE"

@dataclass
class HandshakeStatus:
    node_id: str
    lambda2: float
    vibration_g: float
    trigger: Optional[SafetyTrigger]
    pre_ack_valid: bool = False

# ============================================================================
# TZINOR HANDSHAKE MONITOR
# ============================================================================

class TzinorHandshakeMonitor:
    def __init__(self, node_id: str = "TZ-01"):
        self.node_id = node_id
        self._phases = np.random.uniform(0, 2*np.pi, 10)
        self._omega = np.random.normal(0, 0.01, 10)
        self.log = []

    def _kuramoto_step(self, K: float = 2.0, vibra: float = 0.0):
        """Simulates synchronization with vibration-induced noise."""
        noise = np.random.normal(0, vibra, 10)
        z = np.mean(np.exp(1j * self._phases))
        phase_z = np.angle(z)
        coupling = K * np.sin(phase_z - self._phases)
        self._phases += (self._omega + coupling + noise)
        self._phases %= (2*np.pi)

    def evaluate_safety(self, lambda2: float, vibra: float) -> Optional[SafetyTrigger]:
        if lambda2 < 0.70:
            return SafetyTrigger.ABORT
        if lambda2 < LAMBDA2_CRIT or vibra > 0.3:
            return SafetyTrigger.DEGRADE
        if vibra > 0.1:
            return SafetyTrigger.PAUSE
        if vibra > VIBRA_THRESHOLD:
            return SafetyTrigger.BUFFER
        return None

    def run_monitor(self, steps: int = 50):
        print(f"🛡️ Starting Handshake Monitor for {self.node_id} (Synapse {SYNAPSE_ID})...")

        current_vibra = 0.02
        for i in range(steps):
            # Gradually increase vibration for simulation
            if i > 30: current_vibra = 0.08
            if i > 45: current_vibra = 0.35

            self._kuramoto_step(vibra=current_vibra)
            z = np.mean(np.exp(1j * self._phases))
            lambda2 = float(np.abs(z))

            trigger = self.evaluate_safety(lambda2, current_vibra)
            status = HandshakeStatus(
                node_id=self.node_id,
                lambda2=lambda2,
                vibration_g=current_vibra,
                trigger=trigger,
                pre_ack_valid=(lambda2 > 0.9)
            )

            if trigger:
                print(f"  [Step {i:02d}] WARNING: {trigger} trigger active (λ₂={lambda2:.4f}, vibra={current_vibra:.2g}g)")

            self.log.append({
                "step": i,
                "lambda2": status.lambda2,
                "vibration_g": status.vibration_g,
                "trigger": status.trigger.value if status.trigger else None,
                "pre_ack_valid": status.pre_ack_valid
            })

        final_lambda2 = self.log[-1]["lambda2"]
        results = {
            "synapse_id": SYNAPSE_ID,
            "node_id": self.node_id,
            "final_lambda2": final_lambda2,
            "max_vibration": max(l["vibration_g"] for l in self.log),
            "safety_status": "CRITICAL" if final_lambda2 < 0.8 else "STABLE",
            "log": self.log[-10:] # Last 10 steps for report
        }

        with open("tzinor_handshake_monitor_results.json", "w") as f:
            json.dump(results, f, indent=2)

        return results

if __name__ == "__main__":
    monitor = TzinorHandshakeMonitor()
    res = monitor.run_monitor()
    print(f"✅ Handshake Monitor complete: λ₂ = {res['final_lambda2']:.4f}, Status: {res['safety_status']}")
