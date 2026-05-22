import os
import json
import importlib.util

def load_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_substrato_486_hybrid_accelerator_canonize():
    file_path = "substrates/400-499_advanced/substrato_486_hybrid_accelerator/substrato_486_hybrid_accelerator.py"
    module = load_module_from_path("substrato_486_hybrid_accelerator", file_path)

    substrate = module.Substrato486HybridAccelerator()
    report_path = substrate.canonize()

    assert os.path.exists(report_path)

    with open(report_path, "r") as f:
        data = json.load(f)

    assert "SEAL_486_HYBRID_ACCELERATOR" in data
    assert "Hash" in data["SEAL_486_HYBRID_ACCELERATOR"]
    assert "Phi_C" in data["SEAL_486_HYBRID_ACCELERATOR"]
    assert data["SEAL_486_HYBRID_ACCELERATOR"]["Accelerated"] == True

    os.remove(report_path)
