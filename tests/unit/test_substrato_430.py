import os
import json
import importlib.util

def load_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_substrato_430_blue_mobile_canonize():
    file_path = "substrates/400-499_advanced/substrato_430_blue_mobile/substrato_430_blue_mobile.py"
    module = load_module_from_path("substrato_430_blue_mobile", file_path)

    substrate = module.Substrato430BlueMobile()
    json_path, img_path = substrate.canonize()

    assert os.path.exists(json_path)
    assert os.path.exists(img_path)

    with open(json_path, "r") as f:
        data = json.load(f)

    assert data["Substrate"] == "430-BLUE-MOBILE"
    assert "Phi_C" in data
    assert "Seal" in data
    assert "Artifact" in data
    assert "Specs" in data
    assert "Total_Pipeline_Time_ns" in data
    assert "Total_Power_mW" in data

    os.remove(json_path)
    os.remove(img_path)
