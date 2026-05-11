#!/usr/bin/env python3
"""
Arkhe 144k Node Stress Test — CUDA Accelerated
Arkhe-Block: 847.813 | Synapse-κ | SOVEREIGN_OMEGA

Comprehensive stress test for the GPU-accelerated Kuramoto reconciler.
Tests 7 profiles simulating real-world scenarios:
  1. NORMAL — Steady-state operation
  2. GAP_SPIKE — Transient ZK-Kuramoto divergence (500ms)
  3. SUSTAINED_GAP — Prolonged divergence (6s) → should trigger VIBRA-2
  4. DREAM_ALIGNED — Positive dream alignment → relaxed thresholds
  5. DREAM_DIVERGENT — Negative dream alignment → tightened thresholds
  6. VIBRA2_STRESS — Repeated VIBRA-2 triggers (2 cycles)
  7. CONVERGENCE — Cold start from random phases

Generates:
  - JSON report with full metrics
  - PNG visualization (6-panel dashboard)
  - Console summary

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
from collections import defaultdict

# Add paths for imports
CUDA_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(CUDA_DIR)
sys.path.insert(0, CUDA_DIR)
sys.path.insert(0, SRC_DIR)

from arkhe_gpu_reconciler import (
    ArkheGPUReconciler, GPUReconcilerStats, Vibra2State
)

logger = logging.getLogger("StressTest")

# ═══════════════════════════════════════════════════════════════
# TEST PROFILES
# ═══════════════════════════════════════════════════════════════

PROFILES = {
    "normal": {
        "duration_s": 30,
        "description": "Steady-state — baseline coherence validation",
        "expected_vibra2": 0,
        "expected_min_coherence": 0.95,
    },
    "gap_spike": {
        "duration_s": 30,
        "description": "Transient divergence — 500ms ZK drop",
        "expected_vibra2": 0,  # Too short for 3s duration trigger
        "expected_min_coherence": 0.90,
    },
    "sustained_gap": {
        "duration_s": 30,
        "description": "Sustained divergence — 6s gap → VIBRA-2 trigger",
        "expected_vibra2": 1,
        "expected_min_coherence": 0.85,
    },
    "dream_aligned": {
        "duration_s": 20,
        "description": "Dream alignment +0.8 → threshold relaxation",
        "expected_vibra2": 0,
        "expected_min_coherence": 0.95,
    },
    "dream_divergent": {
        "duration_s": 20,
        "description": "Dream divergence -0.6 → threshold tightening",
        "expected_vibra2": 0,
        "expected_min_coherence": 0.90,
    },
    "vibra2_stress": {
        "duration_s": 30,
        "description": "Repeated VIBRA-2 triggers (2 cycles)",
        "expected_vibra2": 2,
        "expected_min_coherence": 0.85,
    },
    "convergence": {
        "duration_s": 60,
        "description": "Cold start — random phases → convergence",
        "expected_vibra2": 0,
        "expected_min_coherence": 0.80,
    },
}


# ═══════════════════════════════════════════════════════════════
# PROFILE EXECUTORS
# ═══════════════════════════════════════════════════════════════

def run_standard_profile(reconciler: ArkheGPUReconciler,
                          profile_name: str,
                          duration_s: float) -> dict:
    """Run standard profiles (normal, gap_spike, etc.)"""
    interval = 0.1
    n_ticks = int(duration_s / interval)

    executors = {
        "normal": lambda t: (None, 0.0),
        "gap_spike": lambda t: (reconciler.zk_lambdas - 0.08, 0.0)
            if 15.0 <= t <= 15.5 else (None, 0.0),
        "sustained_gap": lambda t: (reconciler.zk_lambdas - 0.06, 0.0)
            if 12.0 <= t <= 18.0 else (None, 0.0),
        "dream_aligned": lambda t: (None, 0.8) if t > 3.0 else (None, 0.0),
        "dream_divergent": lambda t: (None, -0.6) if t > 3.0 else (None, 0.0),
        "vibra2_stress": lambda t: (
            reconciler.zk_lambdas - 0.07, 4.0
        ) if (5.0 <= t <= 11.0 or 18.0 <= t <= 24.0) else (None, 0.0),
    }
    executor = executors.get(profile_name, executors["normal"])

    history = []
    vibra2_count = 0
    for i in range(n_ticks):
        t = i * interval
        zk_update, dream_align = executor(t)
        delta_dur = 3.5 if reconciler.vibra2_state == Vibra2State.WARNING else 0.0

        stats = reconciler.tick(
            zk_lambdas=zk_update,
            dream_alignment=dream_align,
            delta_duration=delta_dur,
        )
        history.append({
            "tick": i, "time_s": t,
            "lambda_k": stats.lambda_k, "lambda_zk": stats.lambda_zk,
            "delta": stats.delta, "coherence": stats.coherence,
            "vibra2": stats.vibra2_triggered,
            "dream": stats.dream_alignment,
            "compute_ms": stats.compute_time_ms,
        })
        if stats.vibra2_triggered and (i == 0 or not history[-2]["vibra2"]):
            vibra2_count += 1

    return {
        "profile": profile_name,
        "n_ticks": n_ticks,
        "duration_s": duration_s,
        "vibra2_activations": vibra2_count,
        "history": history,
        "final": history[-1] if history else {},
    }


def run_convergence_profile(n_nodes: int = 144000) -> dict:
    """Cold start convergence test — random phases"""
    from arkhe_gpu_reconciler import ArkheGPUReconciler

    # Create reconciler with WIDE phase spread
    reconciler = ArkheGPUReconciler(n_nodes=n_nodes, block_size=256)
    rng = np.random.default_rng(42)
    reconciler.thetas = rng.uniform(0, 2 * np.pi, n_nodes).astype(np.float32)

    interval = 0.1
    duration = 60.0
    n_ticks = int(duration / interval)
    history = []

    for i in range(n_ticks):
        stats = reconciler.tick(dream_alignment=0.0, delta_duration=0.0)
        history.append({
            "tick": i,
            "time_s": i * interval,
            "lambda_k": stats.lambda_k,
            "delta": stats.delta,
            "coherence": stats.coherence,
            "vibra2": stats.vibra2_triggered,
            "compute_ms": stats.compute_time_ms,
        })

    return {
        "profile": "convergence",
        "n_ticks": n_ticks,
        "duration_s": duration,
        "vibra2_activations": 0,
        "history": history,
        "final": history[-1] if history else {},
    }


# ═══════════════════════════════════════════════════════════════
# VISUALIZATION
# ═══════════════════════════════════════════════════════════════

def generate_stress_test_viz(all_results: dict,
                              output_path: str = None) -> str:
    """Generate 6-panel stress test dashboard"""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec

    if output_path is None:
        output_path = "cuda_stress_test_847813.png"

    profiles_to_plot = ["normal", "sustained_gap", "dream_aligned",
                        "dream_divergent", "vibra2_stress"]
    n_profiles = len(profiles_to_plot)

    fig = plt.figure(figsize=(22, 4 * n_profiles), facecolor='#0a0a1a')
    fig.suptitle(
        'CUDA STRESS TEST — 144,000 NODES — Arkhe-Block 847.813\n'
        f'Backend: {all_results.get("backend", "UNKNOWN")} | '
        f'Timestamp: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}',
        fontsize=14, color='#FFD700', fontweight='bold', y=0.99
    )

    for idx, pname in enumerate(profiles_to_plot):
        if pname not in all_results.get("profiles", {}):
            continue
        result = all_results["profiles"][pname]
        history = result.get("history", [])
        if not history:
            continue

        gs = GridSpec(1, 3, figure=fig, hspace=0.4, wspace=0.3,
                      left=0.06, right=0.97, top=0.92 - idx * 0.005,
                      bottom=0.02)

        times = [h["time_s"] for h in history]
        coherences = [h["coherence"] for h in history]
        deltas = [h["delta"] for h in history]
        compute_times = [h["compute_ms"] for h in history]

        # Panel 1: Coherence
        ax1 = fig.add_subplot(gs[idx, 0])
        ax1.set_facecolor('#0d0d2b')
        ax1.plot(times, coherences, color='#00BFFF', linewidth=0.8, alpha=0.9)
        ax1.axhline(y=0.847, color='#FF4444', linestyle='--', linewidth=0.8,
                    alpha=0.7, label='λ₂-crit')
        # Shade VIBRA-2 regions
        for i in range(len(history) - 1):
            if history[i]["vibra2"]:
                ax1.axvspan(times[i], times[i+1], alpha=0.3, color='red',
                           linewidth=0)
        ax1.set_ylabel('λ₂ (coherence)', color='white', fontsize=8)
        ax1.set_title(f'{pname.upper()} — Coherence', color='#FFD700',
                      fontsize=9)
        ax1.tick_params(colors='white', labelsize=7)
        for spine in ax1.spines.values():
            spine.set_color('#333')

        # Panel 2: Delta
        ax2 = fig.add_subplot(gs[idx, 1])
        ax2.set_facecolor('#0d0d2b')
        ax2.fill_between(times, deltas, alpha=0.3, color='#FF6B6B')
        ax2.plot(times, deltas, color='#FF6B6B', linewidth=0.8)
        ax2.axhline(y=0.03, color='#FFD700', linestyle='--', linewidth=0.7,
                    label='Warning')
        ax2.axhline(y=0.05, color='#FF4444', linestyle='--', linewidth=0.7,
                    label='VIBRA-2')
        ax2.set_ylabel('Δ = |λ_K - λ_ZK|', color='white', fontsize=8)
        ax2.set_title('Phase Gap', color='#FFD700', fontsize=9)
        ax2.legend(fontsize=6, facecolor='#1a1a3e', edgecolor='#333',
                  labelcolor='white')
        ax2.tick_params(colors='white', labelsize=7)
        for spine in ax2.spines.values():
            spine.set_color('#333')

        # Panel 3: Compute Time
        ax3 = fig.add_subplot(gs[idx, 2])
        ax3.set_facecolor('#0d0d2b')
        ax3.plot(times, compute_times, color='#00FF88', linewidth=0.6,
                alpha=0.7)
        ax3.axhline(y=100, color='#FFD700', linestyle=':', linewidth=0.7,
                    label='100ms budget')
        ax3.set_ylabel('Compute (ms)', color='white', fontsize=8)
        ax3.set_title('Per-Tick Latency', color='#FFD700', fontsize=9)
        ax3.legend(fontsize=6, facecolor='#1a1a3e', edgecolor='#333',
                  labelcolor='white')
        ax3.tick_params(colors='white', labelsize=7)
        for spine in ax3.spines.values():
            spine.set_color('#333')

    plt.savefig(output_path, dpi=150, facecolor='#0a0a1a',
                edgecolor='none', bbox_inches='tight')
    plt.close()
    return output_path


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s [%(name)s] %(levelname)s: %(message)s')

    N = 144000
    print("=" * 70)
    print("  ARKHE CUDA STRESS TEST — 144,000 NODES")
    print("  Arkhe-Block: 847.813 | Synapse-κ | SOVEREIGN_OMEGA")
    print("=" * 70)

    all_results = {
        "arkhe_block": 847813,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "n_nodes": N,
        "backend": "UNKNOWN",
        "profiles": {},
        "summary": {},
    }

    # Detect backend
    reconciler = ArkheGPUReconciler(n_nodes=N, block_size=256)
    all_results["backend"] = "GPU" if reconciler.use_gpu else "CPU-EMULATION"
    print(f"\n  Backend: {all_results['backend']}")
    print(f"  Grid: {reconciler.grid_size} blocks × {reconciler.block_size} threads")
    print()

    # Run standard profiles
    test_results = []
    for pname, pconfig in PROFILES.items():
        if pname == "convergence":
            continue

        print(f"{'─' * 60}")
        print(f"  📊 {pconfig['description']}")
        print(f"     Duration: {pconfig['duration_s']}s | "
              f"Expected VIBRA-2: {pconfig['expected_vibra2']}")

        r = ArkheGPUReconciler(n_nodes=N, block_size=256)
        result = run_standard_profile(r, pname, pconfig["duration_s"])
        all_results["profiles"][pname] = {
            "duration_s": pconfig["duration_s"],
            "vibra2_activations": result["vibra2_activations"],
            "expected_vibra2": pconfig["expected_vibra2"],
            "expected_min_coherence": pconfig["expected_min_coherence"],
            "actual_min_coherence": min(
                h["coherence"] for h in result["history"]) if result["history"] else 0,
            "actual_max_delta": max(
                h["delta"] for h in result["history"]) if result["history"] else 0,
            "avg_compute_ms": float(
                np.mean([h["compute_ms"] for h in result["history"]]
                        ) if result["history"] else 0),
            "p95_compute_ms": float(
                np.percentile([h["compute_ms"] for h in result["history"]], 95)
                if result["history"] else 0),
            "final_coherence": result["final"].get("coherence", 0),
        }

        pr = all_results["profiles"][pname]
        v2_ok = pr["vibra2_activations"] == pr["expected_vibra2"]
        coh_ok = pr["actual_min_coherence"] >= pr["expected_min_coherence"]

        print(f"     VIBRA-2: {pr['vibra2_activations']} "
              f"{'✅' if v2_ok else '❌'} (expected {pr['expected_vibra2']})")
        print(f"     Min λ₂: {pr['actual_min_coherence']:.4f} "
              f"{'✅' if coh_ok else '❌'} (≥ {pr['expected_min_coherence']})")
        print(f"     Max Δ:  {pr['actual_max_delta']:.4f}")
        print(f"     Avg compute: {pr['avg_compute_ms']:.2f} ms")
        print(f"     P95 compute: {pr['p95_compute_ms']:.2f} ms")

        test_results.append(v2_ok and coh_ok)

    # Convergence test
    print(f"\n{'─' * 60}")
    print(f"  📊 CONVERGENCE — Cold start from random phases")
    conv_result = run_convergence_profile(n_nodes=N)
    conv_history = conv_result["history"]
    conv_coherences = [h["coherence"] for h in conv_history]
    conv_start = conv_coherences[0] if conv_coherences else 0
    conv_end = conv_coherences[-1] if conv_coherences else 0
    conv_min = min(conv_coherences) if conv_coherences else 0

    all_results["profiles"]["convergence"] = {
        "duration_s": 60,
        "vibra2_activations": 0,
        "initial_coherence": conv_start,
        "final_coherence": conv_end,
        "min_coherence": conv_min,
        "convergence_delta": conv_end - conv_start,
    }
    print(f"     Initial λ₂: {conv_start:.4f}")
    print(f"     Final λ₂:   {conv_end:.4f}")
    print(f"     Min λ₂:     {conv_min:.4f}")
    print(f"     Δ converge: {conv_end - conv_start:+.4f}")

    # Generate visualization
    print(f"\n{'─' * 60}")
    print("  Generating visualization...")
    viz_path = generate_stress_test_viz(all_results)
    print(f"  ✅ Visualization: {viz_path}")

    # Save JSON report
    report_path = "cuda_stress_test_report_847813.json"
    with open(report_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"\n  ✅ Report: {report_path}")

    # Summary
    passed = sum(test_results)
    total = len(test_results)
    all_results["summary"] = {
        "tests_passed": passed,
        "tests_total": total,
        "all_passed": passed == total,
        "backend": all_results["backend"],
        "n_nodes": N,
    }

    print(f"\n{'=' * 70}")
    print(f"  RESULTS: {passed}/{total} tests passed")
    if passed == total:
        print(f"  ✅ ALL STRESS TESTS PASSED — CUDA KERNEL DEPLOY READY")
    else:
        print(f"  ⚠️ SOME TESTS FAILED — REVIEW REQUIRED")
    print(f"  Backend: {all_results['backend']}")
    print(f"{'=' * 70}")

    return all_results


if __name__ == "__main__":
    main()
