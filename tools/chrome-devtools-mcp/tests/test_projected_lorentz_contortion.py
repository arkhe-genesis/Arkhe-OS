import numpy as np
import pytest
from core.dynamics.projected_lorentz_contortion import ContortionTensor, ProjectedLorentzContortion

def chronometric_phase_tau(tau: float, lambda_delta: float = 3722/2705, tau0: float = 1.0) -> float:
    return np.sin(lambda_delta * tau / tau0)

def test_contortion_tensor_decomposition():
    components = np.random.randn(4, 4)
    K = ContortionTensor(components)

    # Reconstruct from components
    reconstructed = (K.trace / 4) * np.eye(4) + K.antisymmetric + K.symmetric_traceless

    assert np.allclose(K.components, reconstructed)

def test_exact_rest_mass_preservation():
    components = np.random.randn(4, 4) * 1e-15
    K = ContortionTensor(components)
    dyn = ProjectedLorentzContortion(K, chronometric_phase_tau)

    c = 299792458.0
    u = np.array([c, 0.0, 0.0, 0.0]) # At rest
    m = 1.0
    p = m * u
    F_ext = np.array([0.0, 10.0, 0.0, 0.0])

    assert dyn.verify_mass_preservation(u, p)

def test_projected_acceleration():
    components = np.random.randn(4, 4) * 1e-15
    K = ContortionTensor(components)
    dyn = ProjectedLorentzContortion(K, chronometric_phase_tau)

    c = 299792458.0
    gamma = 1.25
    v = np.sqrt(1 - 1/gamma**2) * c
    u = np.array([gamma * c, gamma * v, 0.0, 0.0])

    m = 1.0
    p = m * u
    F_ext = np.array([0.0, 10.0, 0.0, 0.0])

    dp_dtau, p_new = dyn.compute_acceleration(u, p, F_ext, tau=1.0, dt=1e-6)

    eta = np.diag([1, -1, -1, -1])
    u_lower = eta @ u
    assert np.abs(u_lower @ dp_dtau) < 1e-5

def test_lambda_delta_derivation():
    from core.dynamics.lambda_delta_derivation import derive_lambda_delta
    val = derive_lambda_delta()
    target = 3722/2705
    assert abs(val - target) < 1e-3

def test_negative_dwell_time():
    from core.dynamics.torsion_resonance_experiment import compute_negative_dwell_time
    dwell_time = compute_negative_dwell_time(1.0, 0.5, 0, 1)
    assert dwell_time < 0
