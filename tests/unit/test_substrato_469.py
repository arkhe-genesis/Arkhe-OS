import os
import json
import importlib.util

def load_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_substrato_469_gyrotron_fab():
    file_path = "substrates/400-499_advanced/substrato_469_gyrotron_fab/substrato_469_gyrotron_fab.py"
    module = load_module_from_path("substrato_469_gyrotron_fab", file_path)

    report_path = module.canonize()
    assert os.path.exists(report_path)

    with open(report_path, "r") as f:
        data = json.load(f)

    assert "SUBSTRATO_469_GYROTRON_FAB" in data
    assert data["SUBSTRATO_469_GYROTRON_FAB"]["Hash"] == "a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2"
    assert data["SUBSTRATO_469_GYROTRON_FAB"]["Phi_C"] == 0.997

    os.remove(report_path)
