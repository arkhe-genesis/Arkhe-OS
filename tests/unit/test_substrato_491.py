import os
import json
import importlib.util

def load_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_substrato_491_agi_cortex_canonize():
    file_path = "substrates/400-499_advanced/substrato_491_agi_cortex/substrato_491_agi_cortex.py"
    module = load_module_from_path("substrato_491_agi_cortex", file_path)

    substrate = module.Substrato491AGICortex()
    report_path = substrate.canonize()

    assert os.path.exists(report_path)

    with open(report_path, "r") as f:
        data = json.load(f)

    assert "SEAL_491_AGI_CORTEX" in data
    seal_data = data["SEAL_491_AGI_CORTEX"]

    assert "Hash" in seal_data
    assert seal_data["Hash"] == "7dae3d221346ed03a7bc30c1f64a5076b285b5f3007e7882ae5d7527eeff36bd"

    assert "Phi_C" in seal_data
    assert seal_data["Phi_C"] == 0.956000

    assert "Phi" in seal_data
    assert seal_data["Phi"] == 2.3

    assert "Status" in seal_data
    assert seal_data["Status"] == "CANONIZED"

    assert "Optimized" in seal_data
    assert seal_data["Optimized"] == True

    os.remove(report_path)
