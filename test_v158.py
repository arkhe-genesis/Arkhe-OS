import numpy as np
from performance_report import PerformanceReport, ReportMeta

def test_performance_report():
    meta = ReportMeta(
        orchestrator_version="158.0",
        simulation_timestamp="2026-05-06T12:00:00Z",
        num_nodes=10,
        num_electrons=50,
        kolmogorov_limit=15.0,
        total_steps=100
    )

    sim_data = {
        'step_energies': np.linspace(10, 20, 100).tolist(),
        'step_gaps': np.linspace(5, 0.1, 100).tolist(),
        'tx_interval_history': np.full(100, 30.0).tolist(),
        'sf_history': np.full(100, 9).tolist(),
        'gap_matrix': np.random.rand(10, 100).tolist()
    }

    report = PerformanceReport(sim_data, meta)
    metrics = report.run(output_dir="test_out")

    assert metrics['convergence']['kolmogorov_reached'] == True
    assert metrics['coherence']['final_avg_gap'] < 1.0
    print("All tests passed.")

if __name__ == "__main__":
    test_performance_report()
