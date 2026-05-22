import os
import json
import importlib.util

def load_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_substrato_485_holographic_projector_canonize():
    file_path = "substrates/400-499_advanced/substrato_485_holographic_projector/substrato_485_holographic_projector.py"
    module = load_module_from_path("substrato_485_holographic_projector", file_path)

    substrate = module.Substrato485HolographicProjector()
    report_path = substrate.canonize()

    assert os.path.exists(report_path)

    with open(report_path, "r") as f:
        data = json.load(f)

    assert "SEAL_485_HOLOGRAPHIC_PROJECTOR" in data
    assert "Hash" in data["SEAL_485_HOLOGRAPHIC_PROJECTOR"]
    assert "Phi_C" in data["SEAL_485_HOLOGRAPHIC_PROJECTOR"]
    assert data["SEAL_485_HOLOGRAPHIC_PROJECTOR"]["Projected"] == True

    os.remove(report_path)
