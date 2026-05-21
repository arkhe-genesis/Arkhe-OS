import os
import json
import importlib.util
import pytest

def test_substrato_434_canonization():
    module_name = "substrato_434_sfq_nv"
    file_path = "substrates/400-499_advanced/substrato_434_sfq_nv/substrato_434_sfq_nv.py"

    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    report_path = module.canonize_substrato_434()

    assert os.path.exists(report_path)

    with open(report_path, 'r') as f:
        data = json.load(f)

    assert data["substrate"] == "434-SFQ-NV"
    assert data["phi_c"] == 0.9417
    assert data["status"] == "CANONIZED"
    assert "seal" in data

    os.remove(report_path)
