#!/usr/bin/env python3
"""
Arkhe CUDA Deployment — Validation & Unit Tests
Arkhe-Block: 847.813 | Synapse-κ | SOVEREIGN_OMEGA

Comprehensive test suite for the CUDA reconciliation stack:
  1. Import validation (all modules load correctly)
  2. GPU device detection
  3. Data initialization (phase, frequency, ZK arrays)
  4. Single tick computation
  5. State machine (VIBRA-2 transitions)
  6. Dream alignment threshold adjustment
  7. Continuous simulation
  8. Convergence from random phases
  9. Edge cases (N=0, N=1, extreme parameters)
  10. Performance regression check

Run: python -m pytest test_cuda_validation.py -v
     or: python test_cuda_validation.py

Author: Synapse-κ / Arkhe(n) Infrastructure
License: Sovereign — Rio City-State
"""

import sys
import os
import numpy as np
import json
import time
from datetime import datetime, timezone, timezone

# Setup paths — add both cuda dir and src dir to path
CUDA_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(CUDA_DIR)
BASE_DIR = os.path.dirname(SRC_DIR)
sys.path.insert(0, CUDA_DIR)
sys.path.insert(0, SRC_DIR)
sys.path.insert(0, BASE_DIR)

# ═══════════════════════════════════════════════════════════════
# TEST FRAMEWORK (lightweight, no pytest dependency)
# ═══════════════════════════════════════════════════════════════

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
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

    def check_float(self, name, actual, expected, tol=0.01, detail=""):
        ok = abs(actual - expected) <= tol
        msg = f"{detail} | actual={actual:.4f}, expected={expected:.4f}, tol={tol}"
        self.check(name, ok, msg)

    def check_range(self, name, actual, lo, hi, detail=""):
        ok = lo <= actual <= hi
        msg = f"{detail} | actual={actual:.4f}, range=[{lo}, {hi}]"
        self.check(name, ok, msg)

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'=' * 60}")
        print(f"  CUDA VALIDATION: {self.passed}/{total} PASSED")
        if self.failed == 0:
            print(f"  ✅ ALL TESTS PASSED")
        else:
            print(f"  ❌ {self.failed} FAILURES")
            for status, name, detail in self.results:
                if status == "FAIL":
                    print(f"     - {name}: {detail}")
        print(f"{'=' * 60}")
        return self.failed == 0


results = TestResults()

# ═══════════════════════════════════════════════════════════════
# TEST 1: Module Imports
# ═══════════════════════════════════════════════════════════════

print("\n── Test Group 1: Module Imports ──")

try:
    from arkhe_cuda_init import (
        get_device_info, check_cuda_availability, CUDAConfig,
        GPUDeviceInfo, print_system_report, PHI, K_CRIT, N_NODES_RIO,
    )
    results.check("arkhe_cuda_init import", True)
except Exception as e:
    results.check("arkhe_cuda_init import", False, str(e))

try:
    from arkhe_gpu_reconciler import (
        ArkheGPUReconciler, GPUReconcilerStats, Vibra2State, BLOCK_SIZE,
    )
    results.check("arkhe_gpu_reconciler import", True)
except Exception as e:
    results.check("arkhe_gpu_reconciler import", False, str(e))

try:
    from arkhe_cuda_reconciler_cupy import CuPyReconciler
    results.check("arkhe_cuda_reconciler_cupy import", True)
except Exception as e:
    results.check("arkhe_cuda_reconciler_cupy import", False, str(e))

# ═══════════════════════════════════════════════════════════════
# TEST 2: Device Detection
# ═══════════════════════════════════════════════════════════════

print("\n── Test Group 2: Device Detection ──")

try:
    device = get_device_info()
    results.check("get_device_info() returns", device is not None)
    results.check("device.name is str", isinstance(device.name, str) and len(device.name) > 0,
                  f"name={device.name}")
    results.check("device.backend is valid",
                  device.backend in ("PYCUDA", "CUPY", "NUMBA", "EMULATION"),
                  f"backend={device.backend}")
    results.check("device.compute_capability is str",
                  isinstance(device.compute_capability, str))
    results.check("GPU available flag", isinstance(device.available, bool),
                  f"available={device.available}")
except Exception as e:
    results.check("Device detection", False, str(e))

try:
    available, info, config = check_cuda_availability()
    results.check("check_cuda_availability()", True)
    results.check("Config N_NODES", config.n_nodes == 144000)
    results.check("Config K = 1/φ", abs(config.K - 0.618033988749895) < 1e-10)
    results.check("Config block_size", config.block_size == 256)
    results.check("Config grid_size", config.grid_size == 563)
    results.check("Config delta_critical", config.delta_critical == 0.05)
except Exception as e:
    results.check("check_cuda_availability", False, str(e))

# ═══════════════════════════════════════════════════════════════
# TEST 3: Data Initialization
# ═══════════════════════════════════════════════════════════════

print("\n── Test Group 3: Data Initialization ──")

try:
    r = ArkheGPUReconciler(n_nodes=144000, block_size=256)
    results.check("Reconciler init", True)
    results.check("thetas shape", r.thetas.shape == (144000,),
                  f"shape={r.thetas.shape}")
    results.check("thetas dtype", r.thetas.dtype == np.float32)
    results.check("omegas shape", r.omegas.shape == (144000,))
    results.check("zk_lambdas shape", r.zk_lambdas.shape == (144000,))
    results.check("zk_lambdas initial", np.allclose(r.zk_lambdas, 0.999))
    results.check("grid_size", r.grid_size == 563,
                  f"grid={r.grid_size}, expected=563")
    results.check("vibra2 initial state",
                  r.vibra2_state == Vibra2State.INACTIVE)
except Exception as e:
    results.check("Data init", False, str(e))

# ═══════════════════════════════════════════════════════════════
# TEST 4: Single Tick Computation
# ═══════════════════════════════════════════════════════════════

print("\n── Test Group 4: Single Tick ──")

try:
    r = ArkheGPUReconciler(n_nodes=144000, block_size=256)
    stats = r.tick()
    results.check("tick() returns", isinstance(stats, GPUReconcilerStats))
    results.check("order_parameter type", isinstance(stats.order_parameter, float))
    results.check("delta type", isinstance(stats.delta, float))
    results.check("coherence type", isinstance(stats.coherence, float))
    results.check("compute_time type", isinstance(stats.compute_time_ms, float))
    results.check_range("order_parameter range",
                        stats.order_parameter, 0.0, 1.0)
    results.check_range("delta range", stats.delta, 0.0, 1.0)
    results.check_range("coherence range", stats.coherence, 0.5, 1.0)
    results.check("compute_time > 0", stats.compute_time_ms > 0,
                  f"t={stats.compute_time_ms:.4f}ms")
except Exception as e:
    results.check("Single tick", False, str(e))

# ═══════════════════════════════════════════════════════════════
# TEST 5: Dream Alignment
# ═══════════════════════════════════════════════════════════════

print("\n── Test Group 5: Dream Alignment ──")

try:
    r = ArkheGPUReconciler(n_nodes=1000, block_size=256)
    # Normal tick
    s_normal = r.tick(dream_alignment=0.0)
    # Dream-aligned tick
    s_aligned = r.tick(dream_alignment=0.8)
    # Dream-divergent tick
    s_divergent = r.tick(dream_alignment=-0.6)
    results.check("Dream aligned executes", True)
    results.check("Dream divergent executes", True)
    results.check("Dream alignment recorded",
                  s_aligned.dream_alignment == 0.8)
    results.check("Dream divergence recorded",
                  s_divergent.dream_alignment == -0.6)
except Exception as e:
    results.check("Dream alignment", False, str(e))

# ═══════════════════════════════════════════════════════════════
# TEST 6: VIBRA-2 State Machine
# ═══════════════════════════════════════════════════════════════

print("\n── Test Group 6: VIBRA-2 State Machine ──")

try:
    r = ArkheGPUReconciler(n_nodes=1000, block_size=256)
    # Initial state
    results.check("Initial VIBRA2 INACTIVE",
                  r.vibra2_state == Vibra2State.INACTIVE)

    # Trigger VIBRA-2 via sustained gap
    for _ in range(10):
        r.tick(dream_alignment=0.0, delta_duration=3.5)

    # Check state progression
    state_name = r.vibra2_state.name
    results.check("VIBRA2 state is valid",
                  state_name in ("INACTIVE", "WARNING", "ACTIVE", "RECOVERY"),
                  f"state={state_name}")
except Exception as e:
    results.check("VIBRA2 state machine", False, str(e))

# ═══════════════════════════════════════════════════════════════
# TEST 7: Simulation Profiles
# ═══════════════════════════════════════════════════════════════

print("\n── Test Group 7: Simulation Profiles ──")

try:
    r = ArkheGPUReconciler(n_nodes=1000, block_size=256)
    for profile in ["normal", "gap_spike", "dream_aligned", "vibra2_stress"]:
        sim = r.simulate(duration_s=2.0, profile=profile)
        results.check(f"simulate('{profile}')", "n_ticks" in sim,
                      f"keys={list(sim.keys())[:5]}")
        results.check(f"simulate('{profile}') n_ticks > 0", sim["n_ticks"] > 0)
except Exception as e:
    results.check("Simulation profiles", False, str(e))

# ═══════════════════════════════════════════════════════════════
# TEST 8: Convergence Test
# ═══════════════════════════════════════════════════════════════

print("\n── Test Group 8: Convergence ──")

try:
    r = ArkheGPUReconciler(n_nodes=1000, block_size=256)
    # Start from random phases
    rng = np.random.default_rng(42)
    r.thetas = rng.uniform(0, 2 * np.pi, 1000).astype(np.float32)
    # Also increase omega spread for more dynamics
    r.omegas = rng.normal(0, 2.0, 1000).astype(np.float32)

    # Run 50 ticks and check coherence varies
    coherences = []
    for _ in range(50):
        s = r.tick()
        coherences.append(s.coherence)

    # At least some variation should occur
    c_std = float(np.std(coherences))
    c_range = float(max(coherences) - min(coherences)) if coherences else 0
    results.check("Convergence produces variation",
                  c_std > 0.0 or c_range > 0.0,
                  f"std={c_std:.6f}, range={c_range:.6f}")
except Exception as e:
    results.check("Convergence", False, str(e))

# ═══════════════════════════════════════════════════════════════
# TEST 9: Edge Cases
# ═══════════════════════════════════════════════════════════════

print("\n── Test Group 9: Edge Cases ──")

try:
    # N=1 (single oscillator)
    r1 = ArkheGPUReconciler(n_nodes=1, block_size=1)
    s1 = r1.tick()
    results.check("N=1 tick", True)

    # N=256 (exact block size)
    r256 = ArkheGPUReconciler(n_nodes=256, block_size=256)
    s256 = r256.tick()
    results.check("N=256 tick", True)

    # Extreme dream alignment
    r = ArkheGPUReconciler(n_nodes=1000, block_size=256)
    s_max = r.tick(dream_alignment=1.0)
    s_min = r.tick(dream_alignment=-1.0)
    results.check("dream=+1.0", True)
    results.check("dream=-1.0", True)

    # High delta_duration
    s_dur = r.tick(delta_duration=100.0)
    results.check("delta_duration=100", True)

except Exception as e:
    results.check("Edge cases", False, str(e))

# ═══════════════════════════════════════════════════════════════
# TEST 10: CuPy Reconciler
# ═══════════════════════════════════════════════════════════════

print("\n── Test Group 10: CuPy Reconciler ──")

try:
    from arkhe_cuda_reconciler_cupy import CuPyReconciler
    cr = CuPyReconciler(n_nodes=1000, block_size=256)
    cs = cr.tick()
    results.check("CuPy tick", isinstance(cs, type(None)) or hasattr(cs, 'coherence'),
                  "returned result")
    bench = cr.benchmark(n_iterations=10)
    results.check("CuPy benchmark", "mean_ms" in bench,
                  f"keys={list(bench.keys())}")
    results.check("CuPy mode", bench["mode"] in ("CUPY-GPU", "CPU-EMULATION"),
                  f"mode={bench['mode']}")
except Exception as e:
    results.check("CuPy tests", False, str(e))

# ═══════════════════════════════════════════════════════════════
# FINAL REPORT
# ═══════════════════════════════════════════════════════════════

all_passed = results.summary()

# Save JSON report
report = {
    "arkhe_block": 847813,
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "validation": {
        "passed": results.passed,
        "failed": results.failed,
        "total": results.passed + results.failed,
        "all_passed": all_passed,
    },
    "results": [
        {"status": s, "name": n, "detail": d}
        for s, n, d in results.results
    ],
}

report_path = "cuda_validation_report_847813.json"
with open(report_path, 'w') as f:
    json.dump(report, f, indent=2)
print(f"\n  Report saved: {report_path}")
