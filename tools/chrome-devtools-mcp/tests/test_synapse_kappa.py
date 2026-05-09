import pytest
import numpy as np
from src.physics.synapse_kappa import calculate_adaptive_gain, SynapseKappaEngine

def test_adaptive_gain_regimes():
    # Test Super-radiance regime (W_0 < -0.2)
    gain_super = calculate_adaptive_gain(k=10, N=100, W_0=-0.5)
    # Test Coherent regime (-0.2 <= W_0 < 0)
    gain_coherent = calculate_adaptive_gain(k=10, N=100, W_0=-0.1)
    # Test Collapse regime (W_0 >= 0)
    gain_collapse = calculate_adaptive_gain(k=10, N=100, W_0=0.1)

    assert gain_super < gain_coherent
    assert gain_collapse > gain_coherent

def test_landauer_dissipation():
    engine = SynapseKappaEngine()
    # No error -> no dissipation
    assert engine.calculate_landauer_dissipation(0.0) == 0.0
    # Higher error -> higher dissipation
    d1 = engine.calculate_landauer_dissipation(0.1)
    d2 = engine.calculate_landauer_dissipation(0.5)
    assert d2 > d1

def test_thermal_rectification():
    engine = SynapseKappaEngine()
    factor = engine.thermal_rectification_factor(1.0)
    # Should be high due to anisotropy (1.5 / 0.015 = 100)
    assert factor == 0.99

def test_process_step():
    engine = SynapseKappaEngine()
    result = engine.process_step(k=10, N=100, W_0=-0.15, lambda2=0.95)

    assert "gain" in result
    assert "q_diss_joules" in result
    assert "rectified_heat" in result
    assert result["thermal_safety_margin"] > 0

def test_signal_correlation():
    engine = SynapseKappaEngine()
    # High correlation when signals are similar
    corr_high = engine.correlate_signals(0.9, 0.9, 0.9)
    # Low correlation when signals diverge
    corr_low = engine.correlate_signals(0.9, 0.2, 0.5)
    assert corr_high > corr_low

def test_optical_oracle():
    from src.physics.synapse_kappa import OpticalOracle
    oracle = OpticalOracle()
    result = oracle.run_time_gating_cycle()
    assert "upe_counts" in result
    assert "nv_fluorescence" in result
    assert "atp_luminescence" in result

def test_hbn_functionalizer():
    from src.physics.synapse_kappa import hBNFunctionalizer
    func = hBNFunctionalizer()
    res1 = func.step_insertion(10.0)
    assert res1["distance_nm"] < 50.0

    # Critical distance - loop to get closer
    for _ in range(50):
        res2 = func.step_insertion(1.0)
    assert res2["distance_nm"] < 5.0

def test_spin_interrogator():
    from src.physics.synapse_kappa import SpinInterrogator
    interrogator = SpinInterrogator()
    res = interrogator.run_odmr_sweep()
    assert res["optimal_frequency_hz"] == 2.8742e9
    assert res["wigner_negativity"] == -0.24
    assert res["odmr_contrast"] > 0.2

def test_eads_controller():
    from src.physics.synapse_kappa import EADSController
    ctrl = EADSController()
    # Before transition
    res1 = ctrl.step_fade_in(500)
    assert res1["is_superradiant"] == False

    # After transition
    res2 = ctrl.step_fade_in(2000)
    assert res2["is_superradiant"] == True
    assert res2["atp_cps"] < res1["atp_cps"]
    assert res2["g2_0"] < 0.5

def test_genesis_miner():
    from src.physics.synapse_kappa import GenesisMiner
    miner = GenesisMiner("MT_ALPHA_001")
    qhash = miner.extract_quantum_entropy(-0.42, 100)
    assert qhash.startswith("qhash_MT_ALPHA_001")

    res = miner.mine_block(0.94, qhash)
    assert res["status"] == "IMMORTALIZED"

def test_mesh_controller():
    from src.physics.synapse_kappa import EADSController, MeshController
    master = EADSController()
    slave = EADSController()
    mesh = MeshController()

    mesh.add_node("MT_ALPHA_001", master)
    mesh.add_node("MT_ALPHA_002", slave)

    # Before master is stable
    res1 = mesh.step_mesh(1000)
    assert res1["status"] == "AWAITING_MASTER_STABILITY"

    # Force master to be superradiant
    master.is_superradiant = True
    res2 = mesh.step_mesh(2000)
    assert "mesh_coherence" in res2
    assert res2["coupling"] > 0

def test_swarm_controller():
    from src.physics.synapse_kappa import EADSController, SwarmController
    swarm = SwarmController(topology="TRIANGLE")
    for i in range(3):
        ctrl = EADSController()
        ctrl.is_superradiant = True
        swarm.add_node(f"MT_BETA_00{i+1}", ctrl)

    res = swarm.step_swarm(2000)
    assert res["global_lambda2"] > 0.9
    assert res["frustration"] > 0
