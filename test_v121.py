import pytest
import numpy as np
from scripts.arkhe_cosmic_cmb_delay_tsvf_v121 import CosmicConfig, CosmicSubstrate121, CMBRealBath, CosmicDelayLineMesh, TSVFRetrocausality

def test_v121_pipeline():
    config = CosmicConfig(n_galaxies=10) # Small for fast testing
    substrate = CosmicSubstrate121(config)
    results = substrate.run_full_pipeline()
    assert "cmb" in results
    assert "delay_mesh" in results
    assert "tsvf" in results

def test_cmb_real_bath():
    config = CosmicConfig()
    bath = CMBRealBath(config)

    # Test T_CMB scaling
    assert np.isclose(bath.T_CMB(0), 2.725)
    assert np.isclose(bath.T_CMB(1), 5.45)

    # Test second law preservation logic
    n_screen = {1.42e9: 1e-3}
    dSdt = bath.entropy_flow_rate(n_screen, 0)
    assert dSdt >= 0

def test_cosmic_delay_line():
    config = CosmicConfig(n_galaxies=5)
    mesh = CosmicDelayLineMesh(config)

    # Test lookback time is positive
    t_lb = mesh.lookback_time(1)
    assert t_lb > 0

    # Test fidelity degradation
    g1 = {'z': 1}
    g2 = {'z': 10}
    fid1 = mesh.fidelity(g1)
    fid2 = mesh.fidelity(g2)
    assert fid1 > fid2 # Fidelity is lower at higher redshift for same frequency shift relative to optical depth model used

def test_tsvf_retrocausality():
    config = CosmicConfig()
    tsvf = TSVFRetrocausality(config)

    # Ensure weak value math is solid
    psi = np.array([1, 0])
    chi = np.array([1, 1]) / np.sqrt(2)
    op = np.array([[1, 0], [0, -1]])

    val = tsvf.weak_value(psi, chi, op)
    assert np.isclose(val, 1.0)
