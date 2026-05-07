import numpy as np
import pytest
from arkhe_os.temporal.floquet_driven_qubit import FloquetParameters, FloquetStabilizedQubit

def test_floquet_parameters():
    params = FloquetParameters(omega_d=2*np.pi*1e6, omega_R=2*np.pi*5e6, phase_offset=0.0)
    assert params.omega_d > 0

def test_floquet_qubit_stability():
    params = FloquetParameters(
        omega_d=2*np.pi*1e6,
        omega_R=2*np.pi*5e6,
        phase_offset=0.0
    )
    qubit = FloquetStabilizedQubit(params, gamma_0=1e3)
    gain = qubit.stability_gain()
    assert gain > 1.0
