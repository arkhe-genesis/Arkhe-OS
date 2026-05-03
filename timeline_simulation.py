# ============================================================================
# ARKHE OS v∞.Ω.∇+++.14.3 — Timeline Branching & Convergence Simulation
# Purpose: Measure ε-convergence, merge stability, and PoC consensus robustness
# Extended to Seven-Dimensional Coherence
# ============================================================================

import numpy as np
import matplotlib.pyplot as plt
import time
from consensus_engine_7d import ProofOfCoherenceConsensus7D, CoherenceStake7D, ForkVote7D, CoherenceTensor7D

def generate_epsilon_trajectory(T: int, target: np.ndarray, theta: np.ndarray, cov: np.ndarray) -> np.ndarray:
    """Multi-dimensional Ornstein-Uhlenbeck process simulating mercy gap dynamics with covariance."""
    # Shape: (T, 7) for 7D coherence
    eps = np.zeros((T, 7))
    eps[0] = target

    # Pre-compute Cholesky decomposition of covariance for correlated noise
    L = np.linalg.cholesky(cov)

    for t in range(1, T):
        # Correlated noise
        noise = L @ np.random.randn(7)
        eps[t] = eps[t-1] + theta * (target - eps[t-1]) + noise

    # Clip to reasonable physical bounds based on target
    lower, upper = CoherenceTensor7D.hard_bounds()
    # Allow some drift outside hard bounds to test rejection
    lower_drift = lower - 0.02 * target
    upper_drift = upper + 0.02 * target
    return np.clip(eps, lower_drift, upper_drift)

def run_timeline_simulation(T: int = 500, num_forks: int = 3, seed: int = 42) -> dict:
    np.random.seed(seed)

    target_obj = CoherenceTensor7D.target()
    target = target_obj.to_vector()
    theta = np.array([0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2])

    # 7D Covariance
    stds = CoherenceTensor7D.nominal_stds()
    cov = np.diag(stds**2)
    cov[1, 2] = cov[2, 1] = 0.6 * stds[1] * stds[2]  # latency-power
    cov[4, 5] = cov[5, 4] = 0.4 * stds[4] * stds[5]  # security-privacy
    cov[0, 6] = cov[6, 0] = -0.3 * stds[0] * stds[6]  # phase-interpretability

    # Generate main timeline
    main_epsilon = generate_epsilon_trajectory(T, target, theta, cov)

    # Initialize consensus engine
    consensus = ProofOfCoherenceConsensus7D(consensus_threshold=0.55, odysseus_multiplier=0.3)

    # Register vertices with varying coherence stakes
    for i in range(5):
        # Create history of CoherenceTensor7D objects
        hist_vecs = main_epsilon[-100:] + np.random.randn(100, 7) * (stds * 0.1)
        stake_hist = [CoherenceTensor7D(*vec) for vec in hist_vecs]
        consensus.register_vertex(CoherenceStake7D(f"vertex-{i}", stake_hist))

    # Fork creation & voting
    fork_ids = []
    fork_results = []

    for f in range(num_forks):
        fork_ts = np.random.randint(T//4, 3*T//4)
        fork_id = f"fork-{f:02d}"
        fork_ids.append(fork_id)

        # Fork ε trajectory (drifts differently in 7 dimensions)
        drift = np.random.randn(7) * (stds * 0.2)
        fork_epsilon = main_epsilon[:fork_ts].copy()

        # Extend to T
        fork_epsilon = np.pad(fork_epsilon, ((0, T - fork_ts), (0, 0)), 'edge')
        L = np.linalg.cholesky(cov)
        for t in range(fork_ts, T):
            noise = L @ np.random.randn(7) * 1.5 # more noise in forks
            fork_epsilon[t] = fork_epsilon[t-1] + drift + noise

        # Clip
        lower, upper = CoherenceTensor7D.hard_bounds()
        fork_epsilon = np.clip(fork_epsilon, lower - 0.05 * target, upper + 0.05 * target)

        final_fork_tensor = CoherenceTensor7D(*fork_epsilon[-1])

        # Simulate voting
        votes_for = np.random.binomial(5, p=0.7)  # 70% support baseline
        for i in range(votes_for):
            consensus.cast_vote(fork_id, ForkVote7D(f"vertex-{i}", True, time.time(), b"sig", final_fork_tensor))
        for i in range(votes_for, 5):
            consensus.cast_vote(fork_id, ForkVote7D(f"vertex-{i}", False, time.time(), b"sig", final_fork_tensor))

        # Odysseus insight ratio (super-linear event probability)
        odys_ratio = 1.0 + 0.4 * np.random.exponential(scale=0.5)

        accept, score, dim_scores, reason = consensus.evaluate_merge(
            fork_id,
            odysseus_insight_ratio=odys_ratio,
            fork_coherence=final_fork_tensor
        )

        fork_results.append({
            "id": fork_id,
            "fork_ts": fork_ts,
            "final_epsilon": fork_epsilon[-1], # 7-dimensional
            "consensus_score": float(score),
            "odys_ratio": float(odys_ratio),
            "merged": accept,
            "reason": reason
        })
        consensus.reset_fork(fork_id)

    # Convergence metrics
    convergence_times = []
    for f in fork_results:
        if f["merged"]:
            # Estimate time to cross threshold (simplified)
            conv_time = f["fork_ts"] + int(20 * np.random.uniform(0.5, 1.2))
            convergence_times.append(conv_time)

    # Normalize epsilon drift by stds to make it comparable across varying scale dimensions
    normalized_drift = []
    for r in fork_results:
        diff = (r["final_epsilon"] - target) / stds
        normalized_drift.append(np.linalg.norm(diff))

    return {
        "main_epsilon_std": float(np.mean(np.std(main_epsilon / stds, axis=0))),
        "fork_results": fork_results,
        "merge_success_rate": sum(1 for r in fork_results if r["merged"]) / num_forks,
        "avg_convergence_time": float(np.mean(convergence_times)) if convergence_times else None,
        "avg_epsilon_drift": float(np.mean(normalized_drift))
    }

def visualize_results(results: dict, main_epsilon: np.ndarray, T: int) -> None:
    fig, ax = plt.subplots(1, 2, figsize=(12, 4))

    # Left: ε trajectory (plot normalized L2 norm to handle different scales like latency and phase)
    stds = CoherenceTensor7D.nominal_stds()
    target = CoherenceTensor7D.soft_targets()

    # Normalize main epsilon and target
    normalized_main = main_epsilon / stds
    normalized_target = target / stds

    main_epsilon_norm = np.linalg.norm(normalized_main, axis=1)
    target_norm = np.linalg.norm(normalized_target)

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
    print(f"Main ε std (normalized):       {results['main_epsilon_std']:.4f}")
    print(f"Merge success rate:            {results['merge_success_rate']:.1%}")
    if results['avg_convergence_time']:
        print(f"Avg convergence time:          {results['avg_convergence_time']:.1f} timestamps")
    print(f"Avg ε L2 drift (normalized):   {results['avg_epsilon_drift']:.4f}")
    print("-"*60)
    for r in results["fork_results"]:
        status = "✅ MERGED" if r["merged"] else f"❌ REJECTED ({r['reason']})"
        eps_str = f"Ph:{r['final_epsilon'][0]:.3f} Lat:{int(r['final_epsilon'][1])} Pwr:{int(r['final_epsilon'][2])}"
        print(f"{r['id']:8s} | Created: {r['fork_ts']:4d} | {eps_str} | Score: {r['consensus_score']:.3f} | Odys: {r['odys_ratio']:.2f} | {status}")
    print("="*60 + "\n")

    # Generate plot
    target = CoherenceTensor7D.soft_targets()
    theta = np.array([0.2] * 7)
    stds = CoherenceTensor7D.nominal_stds()
    cov = np.diag(stds**2)
    main_eps = generate_epsilon_trajectory(T, target, theta, cov)
    visualize_results(results, main_eps, T)
