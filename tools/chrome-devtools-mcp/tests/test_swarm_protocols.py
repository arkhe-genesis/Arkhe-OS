import pytest
import numpy as np
from src.physics.sasc_nanobot_engine import NanoBotSwarm, SwarmPMIC
from src.physics.sasc_swarm_orchestrator import ExternalHub, SwarmOrchestrator

def test_pmic_charging():
    pmic = SwarmPMIC(v_th=0.48, i_leak=10e-12, c_store=1e-12)
    # Using 20 pW to get ms-scale charging (matching 1pF and 11.5ms target)
    p_in = 20e-12
    t_charge = pmic.calculate_charge_time(p_in)
    assert 0.010 < t_charge < 0.020 # ~15ms

def test_swarm_sync_convergence():
    # Small swarm for fast test
    swarm = NanoBotSwarm(count=100)
    initial_r = swarm.get_order_parameter()

    # Simulate for more cycles to allow convergence (matching 12s target in prompt)
    # We use a larger dt or more steps.
    dt = 0.01
    for _ in range(2000): # 20 seconds
        swarm.update_iesr_dynamics(dt, 20e-12)
        swarm.distributed_kuramoto_sync(K=20.0, dt=dt)

    final_r = swarm.get_order_parameter()
    assert final_r > initial_r
    assert final_r > 0.7 # High coherence

def test_cervera_protocol_simulation():
    swarm = NanoBotSwarm(count=50)
    hub = ExternalHub()
    orchestrator = SwarmOrchestrator(swarm, hub)

    # Run a short simulation
    results = orchestrator.simulate_tumor_treatment(duration_s=2.0, dt=0.01)

    assert results["final_phase"] in ["PRESCRIPTION", "NORMALIZATION"]
    assert len(results["logs"]) >= 1
    assert "Dissonance detected" in results["logs"][0]

def test_hub_monitoring():
    hub = ExternalHub()
    status = hub.monitor_swarm(r_observed=0.95)
    assert status == "MAX_COHERENCE_REACHED"

    status = hub.monitor_swarm(r_observed=0.5)
    assert status == "SYNC_IN_PROGRESS"
