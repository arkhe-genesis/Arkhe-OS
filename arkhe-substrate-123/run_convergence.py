#!/usr/bin/env python3
# ============================================================================
# ARKHE OS v∞.Ω.∇+++.12.3 — Entry Point: Run Convergence Simulation
# Usage: python run_convergence.py [--optimal-id ID] [--steps N]
# ============================================================================

import argparse
import sys
from simulation.convergence_test import main

def parse_args():
    parser = argparse.ArgumentParser(description="Run UCB1 bandit convergence simulation")
    parser.add_argument("--optimal-id", type=int, default=8,
                       help="ID of ground-truth optimal variant (default: 8)")
    parser.add_argument("--steps", type=int, default=200,
                       help="Number of simulation steps (default: 200)")
    parser.add_argument("--output", type=str, default="simulation/results",
                       help="Output directory for plots and metrics")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()

    # Override defaults if provided
    import simulation.convergence_test as conv_test
    original_run = conv_test.run_convergence_simulation

    def wrapped_run(variants, optimal_id, num_steps, exploration_constant, output_dir):
        return original_run(
            variants=variants,
            optimal_id=args.optimal_id if args.optimal_id != 8 else optimal_id,
            num_steps=args.steps,
            exploration_constant=exploration_constant,
            output_dir=args.output
        )

    conv_test.run_convergence_simulation = wrapped_run

    # Run simulation
    results = main()

    # Exit with appropriate code
    sys.exit(0 if results["final_stats"]["converged"] else 1)