# ============================================================================
# ARKHE OS v∞.Ω.∇+++.12.3 — Bandit Convergence Simulation
# Purpose: Validate UCB1 + mercy-aware reward converges to optimal variant
# ============================================================================

import numpy as np
import matplotlib.pyplot as plt
import logging
from pathlib import Path
from typing import Dict, List

from bandit.kernel_variant import KernelVariant
from bandit.ceremony_reward import CeremonyReward
from bandit.ucb1_bandit import UCB1KernelBandit
from kernelzoo.pdi_zoo import generate_pdi_kernel_zoo
from simulation.telemetry_generator import SyntheticTelemetryGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_convergence_simulation(
    variants: List[KernelVariant],
    optimal_id: int,
    num_steps: int = 200,
    exploration_constant: float = 2.0,
    output_dir: str = "simulation/results"
) -> Dict:
    """
    Run full bandit convergence simulation.

    Args:
        variants: List of KernelVariant instances
        optimal_id: ID of ground-truth optimal variant
        num_steps: Number of bandit iterations to simulate
        exploration_constant: UCB1 exploration parameter C
        output_dir: Directory for saving plots and metrics

    Returns:
        dict with convergence history and final statistics
    """
    # Initialize components
    reward_fn = CeremonyReward()
    bandit = UCB1KernelBandit(
        variants=variants,
        reward_fn=reward_fn,
        exploration_constant=exploration_constant
    )
    telemetry_gen = SyntheticTelemetryGenerator(optimal_id)

    # Tracking history
    history = {
        "step": [],
        "selected_id": [],
        "reward": [],
        "epsilon": [],
        "latency": [],
        "power": [],
        "best_variant": [],
        "mean_reward_best": [],
        "safe_count": [],
        "converged_step": None
    }

    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting convergence simulation: {num_steps} steps, optimal_id={optimal_id}")

    for step in range(num_steps):
        # 1. Select variant via UCB1
        selected_id = bandit.select_variant()

        # 2. Generate synthetic telemetry
        variant = bandit.get_variant(selected_id)
        if variant is None:
            logger.error(f"Variant {selected_id} not found in zoo")
            continue

        latency, power, epsilon = telemetry_gen.generate(variant)

        # 3. Update bandit with telemetry
        reward = bandit.update(selected_id, latency, power, epsilon)

        # 4. Record metrics
        stats = bandit.get_statistics()
        history["step"].append(step)
        history["selected_id"].append(selected_id)
        history["reward"].append(reward)
        history["epsilon"].append(epsilon)
        history["latency"].append(latency)
        history["power"].append(power)
        history["best_variant"].append(stats["best_variant_id"])
        history["mean_reward_best"].append(stats["mean_reward_best"])
        history["safe_count"].append(stats["safe_variant_count"])

        # 5. Early convergence detection
        if history["converged_step"] is None:
            if step > 50 and stats["best_variant_id"] == optimal_id:
                # Check if converged for last 20 steps
                if all(v == optimal_id for v in history["best_variant"][-20:]):
                    history["converged_step"] = step
                    logger.info(f"✓ Converged to optimal variant {optimal_id} at step {step}")

    # 6. Generate plots
    _generate_convergence_plots(history, optimal_id, output_dir)

    # 7. Compute final statistics
    final_stats = {
        "converged": history["converged_step"] is not None,
        "converged_at_step": history["converged_step"],
        "final_reward": history["mean_reward_best"][-1] if history["mean_reward_best"] else 0,
        "epsilon_in_gap_pct": sum(0.04 <= e <= 0.10 for e in history["epsilon"]) / max(len(history["epsilon"]), 1) * 100,
        "safe_variants_final": history["safe_count"][-1] if history["safe_count"] else 0,
        "total_variants": len(variants),
        "avg_latency": np.mean(history["latency"]),
        "avg_power": np.mean(history["power"]),
        "avg_epsilon": np.mean(history["epsilon"])
    }

    # 8. Save metrics to file
    _save_metrics(final_stats, output_dir)

    logger.info(f"Simulation complete. Results saved to {output_dir}/")

    return {
        "history": history,
        "final_stats": final_stats
    }


def _generate_convergence_plots(history: Dict, optimal_id: int, output_dir: str) -> None:
    """Generate convergence visualization plots."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Plot 1: Variant selection over time
    ax = axes[0, 0]
    ax.plot(history["step"], history["selected_id"], label="Selected Variant", alpha=0.7, linewidth=1)
    ax.axhline(y=optimal_id, color='green', linestyle='--', linewidth=2, label=f"Optimal (ID {optimal_id})")
    ax.set_xlabel("Launch Step", fontsize=10)
    ax.set_ylabel("Variant ID", fontsize=10)
    ax.set_title("Variant Selection Over Time", fontsize=12, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, linestyle=':')

    # Plot 2: Reward trajectory
    ax = axes[0, 1]
    ax.plot(history["step"], history["reward"], label="Instant Reward", alpha=0.4, linewidth=0.5)
    # Moving average for smoothing
    window = 10
    if len(history["reward"]) >= window:
        ma_reward = np.convolve(history["reward"], np.ones(window)/window, mode='valid')
        ma_steps = history["step"][window-1:]
        ax.plot(ma_steps, ma_reward, label=f"{window}-step MA", color='red', linewidth=2)
    ax.set_xlabel("Launch Step", fontsize=10)
    ax.set_ylabel("Reward", fontsize=10)
    ax.set_title("Mercy-Aware Reward Convergence", fontsize=12, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, linestyle=':')

    # Plot 3: Epsilon trajectory (mercy gap)
    ax = axes[1, 0]
    ax.plot(history["step"], history["epsilon"], label="ε (mercy gap)", alpha=0.7, linewidth=1, color='purple')
    ax.axhspan(0.04, 0.10, alpha=0.15, color='green', label="Mercy Gap [0.04, 0.10]")
    ax.axhline(y=0.07, color='orange', linestyle=':', linewidth=1.5, label="Target ε=0.07")
    ax.set_xlabel("Launch Step", fontsize=10)
    ax.set_ylabel("Epsilon", fontsize=10)
    ax.set_title("Mercy Gap Preservation", fontsize=12, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, linestyle=':')

    # Plot 4: Best variant mean reward
    ax = axes[1, 1]
    ax.plot(history["step"], history["mean_reward_best"], label="Best Variant Mean Reward", linewidth=2)
    ax.set_xlabel("Launch Step", fontsize=10)
    ax.set_ylabel("Mean Reward", fontsize=10)
    ax.set_title("Convergence to Optimal Performance", fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle=':')

    plt.tight_layout()
    plot_path = Path(output_dir) / "bandit_convergence_pdi.png"
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"✓ Convergence plot saved to {plot_path}")


def _save_metrics(stats: Dict, output_dir: str) -> None:
    """Save final metrics to JSON file."""
    import json
    metrics_path = Path(output_dir) / "convergence_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"✓ Metrics saved to {metrics_path}")


def main():
    """Entry point for convergence simulation."""
    # Generate PDI kernel zoo
    pdi_variants = generate_pdi_kernel_zoo()

    # Select optimal variant (ID 8: block=512, unroll=4, full tile = best balance)
    optimal_variant_id = 8

    # Run simulation
    results = run_convergence_simulation(
        variants=pdi_variants,
        optimal_id=optimal_variant_id,
        num_steps=200,
        exploration_constant=2.0,
        output_dir="simulation/results"
    )

    # Print final statistics
    stats = results["final_stats"]
    print(f"\n{'='*60}")
    print(f"CONVERGENCE SIMULATION RESULTS")
    print(f"{'='*60}")
    print(f"Converged to optimal:     {stats['converged']}")
    if stats['converged']:
        print(f"  → at step:              {stats['converged_at_step']}")
    print(f"Final mean reward:        {stats['final_reward']:.3f}")
    print(f"ε in mercy gap:           {stats['epsilon_in_gap_pct']:.1f}%")
    print(f"Safe variants (final):    {stats['safe_variants_final']}/{stats['total_variants']}")
    print(f"Avg latency:              {stats['avg_latency']:.1f} µs")
    print(f"Avg power:                {stats['avg_power']:.1f} mW")
    print(f"Avg epsilon:              {stats['avg_epsilon']:.3f}")
    print(f"{'='*60}\n")

    return results


if __name__ == "__main__":
    main()