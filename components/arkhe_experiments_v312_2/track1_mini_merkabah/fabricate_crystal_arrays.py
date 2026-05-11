#!/usr/bin/env python3
"""
fabricate_crystal_arrays.py - Arkhe OS v∞.312.2 Track 1 Mini-Merkabah
Script to simulate the fabrication and validation of crystal arrays for N = 16, 24, 32.
"""

import json
import os
import numpy as np

def fabricate_array(N):
    """Simulates the fabrication of a crystal array of size NxN."""
    print(f"Starting fabrication for array size N={N} ({N}x{N} crystals)")

    num_crystals = N * N

    # Simulate fabrication properties for each crystal
    crystals = []
    for i in range(num_crystals):
        crystal = {
            "id": i + 1,
            "resonance_freq_hz": round(np.random.normal(32768, 32768 * 0.01), 2), # 32.768 kHz ± 1%
            "q_factor": int(np.random.normal(1.2e6, 1e5)), # > 10^6
            "kt2_coupling_percent": round(np.random.normal(0.12, 0.01), 3), # > 0.1%
            "dimensions_mm": [
                round(np.random.normal(2.0, 0.005), 3),
                round(np.random.normal(2.0, 0.005), 3),
                round(np.random.normal(0.5, 0.001), 3)
            ]
        }
        crystals.append(crystal)

    # Validate the array
    valid = True
    issues = []

    avg_freq = sum(c["resonance_freq_hz"] for c in crystals) / num_crystals
    if not (32768 * 0.95 <= avg_freq <= 32768 * 1.05):
        valid = False
        issues.append(f"Average resonance frequency ({avg_freq} Hz) out of bounds.")

    low_q_count = sum(1 for c in crystals if c["q_factor"] < 1e6)
    if low_q_count > num_crystals * 0.05: # Allow max 5% with low Q
        valid = False
        issues.append(f"Too many crystals ({low_q_count}) with Q factor < 10^6.")

    return {
        "N": N,
        "total_crystals": num_crystals,
        "valid": valid,
        "issues": issues,
        "avg_resonance_freq_hz": round(avg_freq, 2),
        "avg_q_factor": int(sum(c["q_factor"] for c in crystals) / num_crystals),
        # Save a sample of the first 5 crystals
        "sample_crystals": crystals[:5]
    }

def main():
    target_sizes = [16, 24, 32]
    results_dir = "arkhe_experiments_v312_2/hardware/fabrication_specs"
    os.makedirs(results_dir, exist_ok=True)

    np.random.seed(42) # For reproducible "fabrication"

    all_results = {}

    for N in target_sizes:
        result = fabricate_array(N)
        all_results[f"N_{N}"] = result

        output_file = os.path.join(results_dir, f"array_spec_N{N}.json")
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)

        print(f"Fabrication completed for N={N}. Valid: {result['valid']}.")
        if not result['valid']:
            print(f"  Issues: {result['issues']}")
        print(f"  Specs saved to {output_file}\n")

    print("All requested arrays fabricated and validated.")

if __name__ == "__main__":
    main()
