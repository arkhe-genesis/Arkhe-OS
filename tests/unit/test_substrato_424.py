import os
import json
import importlib.util

def load_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_substrato_424_blue_fab_canonize():
    file_path = "substrates/400-499_advanced/substrato_424_blue_fab/substrato_424_blue_fab.py"
    module = load_module_from_path("substrato_424_blue_fab", file_path)

    substrate = module.Substrato424BlueFab()
    report_path = substrate.canonize()

    assert os.path.exists(report_path)

    with open(report_path, "r") as f:
        data = json.load(f)

    assert "SEAL_424_BLUE_FAB" in data
    assert "Hash" in data["SEAL_424_BLUE_FAB"]
    assert "Phi_C" in data["SEAL_424_BLUE_FAB"]
    assert data["SEAL_424_BLUE_FAB"]["Calibrated"] == True

    os.remove(report_path)
