import pytest
from simulation.convergence_test import run_convergence_simulation
from kernelzoo.pdi_zoo import generate_pdi_kernel_zoo

def test_convergence():
    pdi_variants = generate_pdi_kernel_zoo()
    optimal_id = 8

    results = run_convergence_simulation(
        variants=pdi_variants,
        optimal_id=optimal_id,
        num_steps=50, # Quick test
        exploration_constant=2.0,
        output_dir="arkhe-substrate-123/simulation/test_results"
    )

    assert len(results["history"]["step"]) == 50
    assert results["final_stats"]["total_variants"] == 16
