import pytest
import numpy as np
from arkhe_os.temporal.floquet_driven_qubit import FloquetParameters, FloquetStabilizedQubit
from arkhe_os.quantum.floquet_qec import FloquetSurfaceCode

def test_effective_physical_error_rate():
    # Setup parameters where driving is strong enough to reduce decoherence
    params = FloquetParameters(
        omega_d=2 * np.pi * 1e6,  # 1 MHz
        omega_R=2 * np.pi * 5e6   # 5 MHz
    )
    # Baseline gamma_0
    gamma_0 = 1e3
    qubit = FloquetStabilizedQubit(params, gamma_0=gamma_0)

    # Baseline error rate p_0
    p_0 = 0.005  # 0.5%

    qec = FloquetSurfaceCode(qubit, base_physical_error_rate=p_0)

    # p_eff should be p_0 * (gamma_eff / gamma_0)
    p_eff = qec.get_effective_physical_error_rate()

    gamma_eff = qubit.effective_decoherence_rate()
    expected_p_eff = p_0 * (gamma_eff / gamma_0)

    assert np.isclose(p_eff, expected_p_eff)
    assert p_eff < p_0  # Should be significantly reduced due to stabilization

def test_logical_error_rate():
    params = FloquetParameters(omega_d=10.0, omega_R=5.0)  # Weak stabilization to keep p_eff reasonable for test
    qubit = FloquetStabilizedQubit(params, gamma_0=1.0)

    # Let's say baseline p_0 = 0.005. p_eff will be < 0.005
    qec = FloquetSurfaceCode(qubit, base_physical_error_rate=0.005)

    p_eff = qec.get_effective_physical_error_rate()
    # Ensure p_eff is below threshold (0.01)
    assert p_eff < 0.01

    d = 3
    p_L = qec.calculate_logical_error_rate(distance=d)

    # p_L = 0.1 * (p_eff / 0.01)^((3+1)/2) = 0.1 * (p_eff / 0.01)^2
    expected_p_L = 0.1 * (p_eff / 0.01) ** 2
    assert np.isclose(p_L, expected_p_L)

def test_required_distance_reduction():
    # Compare overhead with and without Floquet stabilization

    # Without stabilization (simulated by omega_R = 0)
    params_no_stab = FloquetParameters(omega_d=1.0, omega_R=0.0)
    qubit_no_stab = FloquetStabilizedQubit(params_no_stab, gamma_0=1.0)
    qec_no_stab = FloquetSurfaceCode(qubit_no_stab, base_physical_error_rate=0.005)

    # With stabilization
    params_stab = FloquetParameters(omega_d=10.0, omega_R=15.0)
    qubit_stab = FloquetStabilizedQubit(params_stab, gamma_0=1.0)
    qec_stab = FloquetSurfaceCode(qubit_stab, base_physical_error_rate=0.005)

    target_p_L = 1e-12

    res_no_stab = qec_no_stab.calculate_required_distance(target_p_L)
    res_stab = qec_stab.calculate_required_distance(target_p_L)

    assert res_stab["required_distance"] < res_no_stab["required_distance"]
    assert res_stab["physical_qubits_per_logical"] < res_no_stab["physical_qubits_per_logical"]

    # Ensure minimum distance is 3
    assert res_stab["required_distance"] >= 3
    # Ensure distance is odd
    assert res_stab["required_distance"] % 2 == 1
