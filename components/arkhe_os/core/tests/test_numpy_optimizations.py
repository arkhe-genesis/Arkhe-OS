import pytest
import numpy as np

@pytest.mark.numpy
def test_jones_representation_vectorized():
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from numpy_optimizations import JonesRepresentationNumPy

    j = JonesRepresentationNumPy()
    res = j.compile_circuit(['σ₁', 'σ₂'])
    assert isinstance(res, complex)

@pytest.mark.numpy
def test_crystal_brain_kuramoto():
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from crystal_brain_numpy import VectorizedKuramoto

    vk = VectorizedKuramoto(n_oscillators=1000, global_coupling=2.0)
    vk.step(dt=0.01)
    op = vk.order_parameter()
    assert abs(op) <= 1.0

@pytest.mark.azure
def test_azure_function_import():
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent.parent.parent))
    import azure_functions.spsa_cycle
    assert True
