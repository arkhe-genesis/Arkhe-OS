import os
import json
import importlib.util

def load_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_substrato_484_lattice_simulator_canonize():
    file_path = "substrates/400-499_advanced/substrato_484_lattice_simulator/substrato_484_lattice_simulator.py"
    module = load_module_from_path("substrato_484_lattice_simulator", file_path)

    substrate = module.Substrato484LatticeSimulator()
    report_path = substrate.canonize()

    assert os.path.exists(report_path)

    with open(report_path, "r") as f:
        data = json.load(f)

    assert "SEAL_484_LATTICE_SIMULATOR" in data
    assert "Hash" in data["SEAL_484_LATTICE_SIMULATOR"]
    assert "Phi_C" in data["SEAL_484_LATTICE_SIMULATOR"]
    assert data["SEAL_484_LATTICE_SIMULATOR"]["Simulated"] == True

    os.remove(report_path)
