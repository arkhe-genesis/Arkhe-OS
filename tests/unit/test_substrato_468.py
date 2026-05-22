import os
import json
import importlib.util

def load_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_substrato_468_gyrotron_qubit():
    file_path = "substrates/400-499_advanced/substrato_468_gyrotron_qubit/substrato_468_gyrotron_qubit.py"
    module = load_module_from_path("substrato_468_gyrotron_qubit", file_path)

    report_path = module.canonize()
    assert os.path.exists(report_path)

    with open(report_path, "r") as f:
        data = json.load(f)

    assert "SUBSTRATO_468_GYROTRON_QUBIT" in data
    assert data["SUBSTRATO_468_GYROTRON_QUBIT"]["Hash"] == "f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1"
    assert data["SUBSTRATO_468_GYROTRON_QUBIT"]["Phi_C"] == 0.994

    os.remove(report_path)
