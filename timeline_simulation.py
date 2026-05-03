# ============================================================================
# ARKHE OS v∞.Ω.∇+++.14.1 — Timeline Branching & Convergence Simulation
# Purpose: Measure ε-convergence, merge stability, and PoC consensus robustness
# Extended to multi-dimensional epsilon (phase, latency, power)
# ============================================================================

import numpy as np
import matplotlib.pyplot as plt
import time
from consensus_engine import ProofOfCoherenceConsensus, CoherenceStake, ForkVote

def generate_epsilon_trajectory(T: int, target: np.ndarray, theta: np.ndarray, sigma: np.ndarray) -> np.ndarray:
    """Multi-dimensional Ornstein-Uhlenbeck process simulating mercy gap dynamics."""
    # Shape: (T, 3) for phase, latency, power
    eps = np.zeros((T, 3))
    eps[0] = target
    for t in range(1, T):
        eps[t] = eps[t-1] + theta * (target - eps[t-1]) + sigma * np.random.randn(3)
    return np.clip(eps, 0.02, 0.12)

def run_timeline_simulation(T: int = 500, num_forks: int = 3, seed: int = 42) -> dict:
    np.random.seed(seed)

    target = np.array([0.07, 0.07, 0.07])
    theta = np.array([0.2, 0.2, 0.2])
    sigma = np.array([0.02, 0.02, 0.02])

    # Generate main timeline
    main_epsilon = generate_epsilon_trajectory(T, target, theta, sigma)

    # Initialize consensus engine
    consensus = ProofOfCoherenceConsensus(consensus_threshold=0.55, odysseus_multiplier=0.3)

    # Register vertices with varying coherence stakes
    for i in range(5):
        stake_hist = main_epsilon[-100:] + np.random.randn(100, 3) * 0.005
        consensus.register_vertex(CoherenceStake(f"vertex-{i}", stake_hist))

    # Fork creation & voting
    fork_ids = []
    fork_results = []

    for f in range(num_forks):
        fork_ts = np.random.randint(T//4, 3*T//4)
        fork_id = f"fork-{f:02d}"
        fork_ids.append(fork_id)

        # Fork ε trajectory (drifts differently in 3 dimensions)
        drift = np.random.choice([-0.01, 0.0, 0.015], size=3)
        fork_epsilon = main_epsilon[:fork_ts].copy()
        # Extend to T
        fork_epsilon = np.pad(fork_epsilon, ((0, T - fork_ts), (0, 0)), 'edge')
        for t in range(fork_ts, T):
            fork_epsilon[t] = fork_epsilon[t-1] + drift + 0.015 * np.random.randn(3)
        fork_epsilon = np.clip(fork_epsilon, 0.02, 0.12)

        # Simulate voting
        votes_for = np.random.binomial(5, p=0.7)  # 70% support baseline
        for i in range(votes_for):
            consensus.cast_vote(fork_id, ForkVote(f"vertex-{i}", True, time.time(), b"sig"), fork_epsilon[-1])
        for i in range(votes_for, 5):
            consensus.cast_vote(fork_id, ForkVote(f"vertex-{i}", False, time.time(), b"sig"), fork_epsilon[-1])

        # Odysseus insight ratio (super-linear event probability)
        odys_ratio = 1.0 + 0.4 * np.random.exponential(scale=0.5)

        accept, score = consensus.evaluate_merge(fork_id, odysseus_insight_ratio=odys_ratio)
        fork_results.append({
            "id": fork_id,
            "fork_ts": fork_ts,
            "final_epsilon": fork_epsilon[-1], # 3-dimensional
            "consensus_score": float(score),
            "odys_ratio": float(odys_ratio),
            "merged": accept
        })
        consensus.reset_fork(fork_id)

    # Convergence metrics
    convergence_times = []
    for f in fork_results:
        if f["merged"]:
            # Estimate time to cross threshold (simplified)
            conv_time = f["fork_ts"] + int(20 * np.random.uniform(0.5, 1.2))
            convergence_times.append(conv_time)

    return {
        "main_epsilon_std": float(np.mean(np.std(main_epsilon, axis=0))),
        "fork_results": fork_results,
        "merge_success_rate": sum(1 for r in fork_results if r["merged"]) / num_forks,
        "avg_convergence_time": float(np.mean(convergence_times)) if convergence_times else None,
        # Calculate mean euclidean distance from target [0.07, 0.07, 0.07]
        "avg_epsilon_drift": float(np.mean([np.linalg.norm(r["final_epsilon"] - target) for r in fork_results]))
    }

def visualize_results(results: dict, main_epsilon: np.ndarray, T: int) -> None:
    fig, ax = plt.subplots(1, 2, figsize=(12, 4))

    # Left: ε trajectory (plot the norm of the 3 dimensions as distance from 0)
    # Target distance from 0 is norm([0.07, 0.07, 0.07]) = ~0.121
    main_epsilon_norm = np.linalg.norm(main_epsilon, axis=1)
    target_norm = np.linalg.norm(np.array([0.07, 0.07, 0.07]))

    ax[0].plot(main_epsilon_norm, label="Main Timeline ε (L2 Norm)", linewidth=2, color="#2b5876")
    ax[0].axhline(target_norm, color="gold", linestyle="--", label=f"Target L2=~{target_norm:.3f}")
    ax[0].fill_between(range(T), target_norm - 0.05, target_norm + 0.05, alpha=0.15, color="green", label="Mercy Gap Region")
    ax[0].set_xlabel("Logical Timestamp")
    ax[0].set_ylabel("Epsilon L2 Norm")
    ax[0].legend()
    ax[0].grid(True, alpha=0.3)

    # Right: Merge outcomes
    merged = [r for r in results["fork_results"] if r["merged"]]
    rejected = [r for r in results["fork_results"] if not r["merged"]]
    ax[1].scatter([r["fork_ts"] for r in merged], [r["consensus_score"] for r in merged],
                  label="Merged (PoC Pass)", color="green", s=80, marker="o")
    ax[1].scatter([r["fork_ts"] for r in rejected], [r["consensus_score"] for r in rejected],
                  label="Rejected", color="red", s=80, marker="x")
    ax[1].axhline(0.55, color="gray", linestyle=":", label="Consensus Threshold")
    ax[1].set_xlabel("Fork Creation Timestamp")
    ax[1].set_ylabel("Consensus Score")
    ax[1].legend()
    ax[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("timeline_convergence_simulation.png", dpi=150)
    print("✓ Simulation plot saved to timeline_convergence_simulation.png")

if __name__ == "__main__":
    T = 500
    results = run_timeline_simulation(T=T)
    print("\n" + "="*60)
    print("TIMELINE BRANCHING SIMULATION RESULTS (Multi-Dimensional)")
    print("="*60)
    print(f"Main ε std (mean across dims): {results['main_epsilon_std']:.4f}")
    print(f"Merge success rate:            {results['merge_success_rate']:.1%}")
    print(f"Avg convergence time:          {results['avg_convergence_time']:.1f} timestamps")
    print(f"Avg ε L2 drift from target:    {results['avg_epsilon_drift']:.4f}")
    print("-"*60)
    for r in results["fork_results"]:
        status = "✅ MERGED" if r["merged"] else "❌ REJECTED"
        eps_str = f"[{r['final_epsilon'][0]:.3f}, {r['final_epsilon'][1]:.3f}, {r['final_epsilon'][2]:.3f}]"
        print(f"{r['id']:8s} | Created: {r['fork_ts']:4d} | ε: {eps_str} | Score: {r['consensus_score']:.3f} | Odys: {r['odys_ratio']:.2f} | {status}")
    print("="*60 + "\n")

    # Generate plot
    target = np.array([0.07, 0.07, 0.07])
    theta = np.array([0.2, 0.2, 0.2])
    sigma = np.array([0.02, 0.02, 0.02])
    main_eps = generate_epsilon_trajectory(T, target, theta, sigma)
    visualize_results(results, main_eps, T)
