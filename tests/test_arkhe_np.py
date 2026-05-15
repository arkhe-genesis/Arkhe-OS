import pytest
from arkhe_np.methods import ArkheNP

def test_arkhe_np_initialization():
    arkhe_np = ArkheNP()
    assert arkhe_np is not None

def test_arkhe_np_methods_exist():
    arkhe_np = ArkheNP()
    assert hasattr(arkhe_np, "run_binsreg")
    assert hasattr(arkhe_np, "run_portsort")
    assert hasattr(arkhe_np, "run_lpdensity")
    assert hasattr(arkhe_np, "run_scpi")

def test_arkhe_np_supported_methods():
    arkhe_np = ArkheNP()
    methods = arkhe_np.get_supported_methods()
    assert len(methods) == 4
    assert "binsreg (Binscatter Methods)" in methods
    assert "scpi (Synthetic Control Methods)" in methods
