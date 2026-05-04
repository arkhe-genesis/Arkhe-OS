import pytest
import numpy as np
from core.dynamics.orbit_residual_simulation import LAMBDA_DELTA, TAU0, K_TENSOR, earth_gravity, contortion_acceleration, full_dynamics

def test_constants():
    assert LAMBDA_DELTA == 3722 / 2705
    assert TAU0 == 86164.0 / (2 * np.pi)
    assert K_TENSOR.shape == (4, 4)

@pytest.mark.numpy
def test_earth_gravity():
    # Test with a state vector [x, y, z, vx, vy, vz]
    state = np.array([6378137.0 + 400000.0, 0, 0, 0, 7600.0, 0])
    deriv = earth_gravity(0, state)
    assert deriv.shape == (6,)
    assert np.allclose(deriv[:3], state[3:]) # dx/dt = v
    # Check acceleration roughly matches Earth gravity
    accel_norm = np.linalg.norm(deriv[3:])
    assert 8.0 < accel_norm < 10.0 # ~8-10 m/s^2 for LEO

@pytest.mark.numpy
def test_contortion_acceleration():
    state = np.array([6378137.0 + 400000.0, 0, 0, 0, 7600.0, 0])
    accel = contortion_acceleration(0, state)
    assert accel.shape == (3,)
    # At t=0, sin(0) = 0, so contortion acceleration should be 0
    assert np.allclose(accel, 0)

    # At t != 0, it should be non-zero
    accel2 = contortion_acceleration(1000, state)
    assert accel2.shape == (3,)
    # Check that magnitude is not zero and very small due to coupling
    assert 0 < np.linalg.norm(accel2) < 1e-10
