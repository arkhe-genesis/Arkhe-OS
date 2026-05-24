import os
import json
import importlib.util

def load_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_substrato_425_blue_gate_canonize():
    file_path = "substrates/400-499_advanced/substrato_425_blue_gate/substrato_425_blue_gate.py"
    module = load_module_from_path("substrato_425_blue_gate", file_path)

    substrate = module.Substrato425BlueGate()
    report_path = substrate.canonize()

    assert os.path.exists(report_path)

    with open(report_path, "r") as f:
        data = json.load(f)

    assert "SEAL_425_BLUE_GATE" in data
    assert "Hash" in data["SEAL_425_BLUE_GATE"]
    assert "Phi_C" in data["SEAL_425_BLUE_GATE"]
    assert "Operation_Simulated" in data["SEAL_425_BLUE_GATE"]

    os.remove(report_path)
