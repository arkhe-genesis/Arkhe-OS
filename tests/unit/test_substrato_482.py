import os
import json
import importlib.util

def load_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_substrato_482_qubo_optimizer_canonize():
    file_path = "substrates/400-499_advanced/substrato_482_qubo_optimizer/substrato_482_qubo_optimizer.py"
    module = load_module_from_path("substrato_482_qubo_optimizer", file_path)

    substrate = module.Substrato482QuboOptimizer()
    report_path = substrate.canonize()

    assert os.path.exists(report_path)

    with open(report_path, "r") as f:
        data = json.load(f)

    assert "SEAL_482_QUBO_OPTIMIZER" in data
    assert "Hash" in data["SEAL_482_QUBO_OPTIMIZER"]
    assert "Phi_C" in data["SEAL_482_QUBO_OPTIMIZER"]
    assert data["SEAL_482_QUBO_OPTIMIZER"]["Optimized"] == True

    os.remove(report_path)
