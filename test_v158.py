import pytest
import numpy as np

def test_convergence_validation():
    from convergence_validation import verify_convergence
    gaps = np.linspace(10, 0.1, 200)
    gaps += np.random.normal(0, 0.05, 200)
    energies = np.linspace(0, 100, 200)
    energies += np.random.normal(0, 1, 200)

    res = verify_convergence(gaps, energies, 90.0)
    assert res['gap_trend']['decreasing'] == True
    assert res['kolmogorov_reached'] == True

def test_performance_report():
    from performance_report import PerformanceReport, ReportMeta

    sim_data = {
        'step_energies': np.linspace(0, 100, 100).tolist(),
        'step_gaps': np.linspace(10, 0.5, 100).tolist(),
        'tx_interval_history': np.ones(100).tolist(),
        'sf_history': np.ones(100).tolist()
    }

    meta = ReportMeta(
        orchestrator_version="v158",
        simulation_timestamp="2026-05-06",
        num_nodes=10,
        num_electrons=5,
        kolmogorov_limit=90.0,
        total_steps=100
    )

    report = PerformanceReport(sim_data, meta)
    res = report.run(output_dir="test-reports")
    assert res['convergence']['kolmogorov_reached'] == True
    assert res['coherence']['final_avg_gap'] == 0.5
