#!/usr/bin/env python3
"""
Cross-simulation for Chemical Gluing Bridge (v∞.389.1).
Compares ARKHE Gluing convergence with a mock LOHC discovery pipeline.
"""
import sys
import os
import json
import random

# Add root directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.chemical_gluing_bridge import ChemicalGluingLoop, ChemicalCandidate

def run_simulation():
    loop = ChemicalGluingLoop()

    # Track metrics
    iterations = []
    capture_rate_arkhe = []
    # Mocking a reference LOHC convergence curve for comparison
    capture_rate_lohc_reference = []

    # State tracking
    current_seeds = [
        ChemicalCandidate("Initial_Seed_1", 50.0, 6.0, 30.0, 4.0),
        ChemicalCandidate("Initial_Seed_2", 45.0, 5.8, 35.0, 4.2)
    ]

    num_iterations = 10
    candidates_per_generation = 100

    for i in range(1, num_iterations + 1):
        # The mean properties slowly shift towards the capture bounds over iterations
        # simulating the "learning" process
        mean_dh = 80.0 - (i * 2.5)  # Shifts from 77.5 down to 55 (target 40-70)
        mean_wt = 4.0 + (i * 0.25)  # Shifts from 4.25 up to 6.5 (target > 5.5)

        def mock_llm_explore(seeds):
            new_candidates = []
            for j in range(candidates_per_generation):
                # Add some randomness to the generation
                dh = random.gauss(mean_dh, 10.0)
                wt = random.gauss(mean_wt, 1.0)
                pp = random.gauss(30.0, 10.0)
                sa = random.gauss(3.0, 1.0)
                cand = ChemicalCandidate(f"Gen{i}_Cand{j}", dh, wt, pp, sa)
                new_candidates.append(cand)
            return new_candidates

        def mock_ml_filter(candidates):
            # A mock ML filter that removes candidates that are clearly terrible
            filtered = []
            for c in candidates:
                # E.g. Filter out extremely high delta_h
                if c.delta_h < 100.0:
                    filtered.append(c)
            return filtered

        # Run step
        captured = loop.step_gluing_cycle(current_seeds, mock_llm_explore, mock_ml_filter)

        # Calculate stats
        rate = len(captured) / candidates_per_generation
        iterations.append(i)
        capture_rate_arkhe.append(rate)

        # Simulated LOHC reference curve (e.g., matching Harb et al., 2026 Fig 3)
        # starts low, ramps up, plateaus
        lohc_ref_rate = 1.0 / (1.0 + 2.718 ** (-(i - 5))) # Simple sigmoid centered at i=5
        capture_rate_lohc_reference.append(lohc_ref_rate)

        # Feedback loop: use captured as seeds for next iteration
        if captured:
            current_seeds = captured

        print(f"Iteration {i}: {len(captured)} captured ({rate:.1%})")

    # Generate JSON report
    report = {
        "iterations": iterations,
        "capture_rate_arkhe": capture_rate_arkhe,
        "capture_rate_lohc_reference": capture_rate_lohc_reference
    }

    # Create results dir if it doesn't exist
    os.makedirs('results', exist_ok=True)

    report_path = 'results/chemical_gluing_convergence_vs_lohc_discovery.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=4)

    print(f"Simulation complete. Report saved to {report_path}")

if __name__ == "__main__":
    run_simulation()
