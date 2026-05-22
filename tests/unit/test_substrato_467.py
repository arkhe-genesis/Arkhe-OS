import os
import json
import importlib.util

def load_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_substrato_467_gyrotron_array():
    file_path = "substrates/400-499_advanced/substrato_467_gyrotron_array/substrato_467_gyrotron_array.py"
    module = load_module_from_path("substrato_467_gyrotron_array", file_path)

    report_path = module.canonize()
    assert os.path.exists(report_path)

    with open(report_path, "r") as f:
        data = json.load(f)

    assert "SUBSTRATO_467_GYROTRON_ARRAY" in data
    assert data["SUBSTRATO_467_GYROTRON_ARRAY"]["Hash"] == "e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0"
    assert data["SUBSTRATO_467_GYROTRON_ARRAY"]["Phi_C"] == 0.996

    os.remove(report_path)
