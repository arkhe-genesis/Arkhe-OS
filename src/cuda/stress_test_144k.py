#!/usr/bin/env python3
"""
Arkhe 144k Node Stress Test — CUDA Accelerated
Arkhe-Block: 847.813 | Synapse-κ | SOVEREIGN_OMEGA

Author: Synapse-κ / Arkhe(n) Infrastructure
License: Sovereign — Rio City-State
"""

import sys
import os
import numpy as np
import json
import logging
import time
from datetime import datetime, timezone, timezone
import matplotlib.pyplot as plt

# Add current directory for direct imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from arkhe_gpu_reconciler import (
    ArkheGPUReconciler, GPUReconcilerStats, Vibra2State
)

logger = logging.getLogger("StressTest")

PROFILES = {
    "normal": {
        "duration_s": 10,
        "description": "Steady-state operation",
        "expected_vibra2": 0,
    },
    "gap_spike": {
        "duration_s": 10,
        "description": "Transient divergence (500ms)",
        "expected_vibra2": 0,
    },
    "sustained_gap": {
        "duration_s": 15,
        "description": "Sustained divergence (6s)",
        "expected_vibra2": 1,
    },
    "dream_aligned": {
        "duration_s": 10,
        "description": "Dream alignment +0.8",
        "expected_vibra2": 0,
    },
    "dream_divergent": {
        "duration_s": 10,
        "description": "Dream divergence -0.6",
        "expected_vibra2": 0,
    },
    "vibra2_stress": {
        "duration_s": 20,
        "description": "Repeated VIBRA-2 triggers",
        "expected_vibra2": 1,
    },
}

def run_standard_profile(reconciler: ArkheGPUReconciler,
                          profile_name: str,
                          duration_s: float) -> dict:
    interval = 0.1
    n_ticks = int(duration_s / interval)

    executors = {
        "normal": lambda t: (None, 0.0),
        "gap_spike": lambda t: (reconciler.zk_lambdas - 0.08, 0.0)
            if 4.0 <= t <= 4.5 else (None, 0.0),
        "sustained_gap": lambda t: (reconciler.zk_lambdas - 0.06, 0.0)
            if 3.0 <= t <= 9.0 else (None, 0.0),
        "dream_aligned": lambda t: (None, 0.8) if t > 2.0 else (None, 0.0),
        "dream_divergent": lambda t: (None, -0.6) if t > 2.0 else (None, 0.0),
        "vibra2_stress": lambda t: (
            reconciler.zk_lambdas - 0.07, 4.0
        ) if (5.0 <= t <= 11.0) else (None, 0.0),
    }
    executor = executors.get(profile_name, executors["normal"])

    history = []
    vibra2_count = 0
    consecutive_warning_s = 0.0

    for i in range(n_ticks):
        t = i * interval
        zk_update, dream_align = executor(t)

        stats = reconciler.tick(
            zk_lambdas=zk_update,
            dream_alignment=dream_align,
            delta_duration=consecutive_warning_s,
        )

        if stats.delta > 0.03:
            consecutive_warning_s += interval
        else:
            consecutive_warning_s = 0.0

        history.append({
            "time_s": t,
            "coherence": stats.coherence,
            "delta": stats.delta,
            "vibra2": stats.vibra2_triggered,
            "compute_ms": stats.compute_time_ms,
        })

        if stats.vibra2_triggered and (i == 0 or not history[-2]["vibra2"]):
            vibra2_count += 1

    return {
        "profile": profile_name,
        "vibra2_activations": vibra2_count,
        "history": history,
    }

def main():
    N = 1000
    all_results = {"profiles": {}}

    fig, axes = plt.subplots(len(PROFILES), 1, figsize=(10, 15), constrained_layout=True)

    for idx, (pname, pconfig) in enumerate(PROFILES.items()):
        print(f"  📊 Running: {pname}")
        r = ArkheGPUReconciler(n_nodes=N)
        res = run_standard_profile(r, pname, pconfig["duration_s"])

        all_results["profiles"][pname] = {
            "vibra2_activations": res["vibra2_activations"],
            "expected": pconfig["expected_vibra2"]
        }

        times = [h["time_s"] for h in res["history"]]
        cohs = [h["coherence"] for h in res["history"]]
        axes[idx].plot(times, cohs, label=f"λ₂ {pname}")
        axes[idx].set_title(pname)
        axes[idx].legend()

    plt.savefig("cuda_stress_test_847813.png")
    with open("cuda_stress_test_report_847813.json", "w") as f:
        json.dump(all_results, f, indent=2)
    print("✅ Stress test complete. Artifacts generated.")

if __name__ == "__main__":
    main()
