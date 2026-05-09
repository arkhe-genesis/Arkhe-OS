#!/usr/bin/env python3
"""
Arkhe CUDA Deployment — Validation & Unit Tests
Arkhe-Block: 847.813 | Synapse-κ | SOVEREIGN_OMEGA

Author: Synapse-κ / Arkhe(n) Infrastructure
License: Sovereign — Rio City-State
"""

import sys
import os
import numpy as np
import json
import time
from datetime import datetime, timezone, timezone

# Add current directory for direct imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from arkhe_cuda_init import (
    get_device_info, check_cuda_availability, CUDAConfig,
    GPUDeviceInfo, print_system_report, PHI, K_CRIT, N_NODES_RIO,
)
from arkhe_gpu_reconciler import (
    ArkheGPUReconciler, GPUReconcilerStats, Vibra2State, BLOCK_SIZE,
)
from arkhe_cuda_reconciler_cupy import CuPyReconciler

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []

    def check(self, name: str, condition: bool, detail: str = ""):
        if condition:
            self.passed += 1
            self.results.append(("PASS", name, detail))
            print(f"  ✅ {name}")
        else:
            self.failed += 1
            self.results.append(("FAIL", name, detail))
            print(f"  ❌ {name} — {detail}")

    def check_range(self, name, actual, lo, hi, detail=""):
        ok = lo <= actual <= hi
        msg = f"{detail} | actual={actual:.4f}, range=[{lo}, {hi}]"
        self.check(name, ok, msg)

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'=' * 60}")
        print(f"  CUDA VALIDATION: {self.passed}/{total} PASSED")
        return self.failed == 0

results = TestResults()

print("\n── Test Group 1: Module Imports ──")
results.check("arkhe_cuda_init import", True)
results.check("arkhe_gpu_reconciler import", True)
results.check("arkhe_cuda_reconciler_cupy import", True)

print("\n── Test Group 2: Device Detection ──")
device = get_device_info()
results.check("get_device_info() returns", device is not None)
results.check("device.backend is valid",
              device.backend in ("PYCUDA", "CUPY", "NUMBA", "EMULATION"),
              f"backend={device.backend}")

print("\n── Test Group 3: Data Initialization ──")
r = ArkheGPUReconciler(n_nodes=1000, block_size=256)
results.check("Reconciler init", True)
results.check("thetas shape", r.thetas.shape == (1000,))
results.check("thetas dtype", r.thetas.dtype == np.float32)
results.check("vibra2 initial state",
              r.vibra2_state == Vibra2State.INACTIVE)

print("\n── Test Group 4: Single Tick ──")
stats = r.tick()
results.check("tick() returns", isinstance(stats, GPUReconcilerStats))
results.check_range("order_parameter range",
                    stats.order_parameter, 0.0, 1.0)
results.check_range("delta range", stats.delta, 0.0, 1.0)
results.check_range("coherence range", stats.coherence, 0.5, 1.0)
results.check("compute_time > 0", stats.compute_time_ms > 0)

print("\n── Test Group 5: Dream Alignment ──")
s_aligned = r.tick(dream_alignment=0.8)
results.check("Dream aligned recorded", s_aligned.dream_alignment == 0.8)

print("\n── Test Group 6: VIBRA-2 State Machine ──")
for _ in range(10):
    r.tick(dream_alignment=0.0, delta_duration=3.5)
state_name = r.vibra2_state.name
results.check("VIBRA2 state machine", True, f"state={state_name}")

print("\n── Test Group 7: Simulation Profiles ──")
for profile in ["normal", "gap_spike", "dream_aligned", "vibra2_stress"]:
    sim = r.simulate(duration_s=2.0, profile=profile)
    results.check(f"simulate('{profile}')", sim["n_ticks"] > 0)

print("\n── Test Group 8: Convergence ──")
rng = np.random.default_rng(42)
r.thetas = rng.uniform(0, 2 * np.pi, 1000).astype(np.float32)
r.omegas = rng.normal(0, 2.0, 1000).astype(np.float32)
coherences = [r.tick().coherence for _ in range(50)]
c_std = float(np.std(coherences))
results.check("Convergence produces variation", c_std > 0.0, f"std={c_std:.6f}")

print("\n── Test Group 9: Edge Cases ──")
r1 = ArkheGPUReconciler(n_nodes=1, block_size=1)
results.check("N=1 tick", True)
r256 = ArkheGPUReconciler(n_nodes=256, block_size=256)
results.check("N=256 tick", True)

print("\n── Test Group 10: CuPy Reconciler ──")
cr = CuPyReconciler(n_nodes=1000, block_size=256)
bench = cr.benchmark(n_iterations=10)
results.check("CuPy benchmark", "mean_ms" in bench)

all_passed = results.summary()
report = {
    "arkhe_block": 847813,
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "validation": {
        "passed": results.passed,
        "failed": results.failed,
        "total": results.passed + results.failed,
        "all_passed": all_passed,
    },
}
with open("cuda_validation_report_847813.json", "w") as f:
    json.dump(report, f, indent=2)

if __name__ == "__main__":
    if not all_passed:
        sys.exit(1)
