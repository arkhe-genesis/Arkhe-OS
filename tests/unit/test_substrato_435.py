import os
import json
import importlib.util

def load_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_substrato_435_orch_yin_yang_canonize():
    file_path = "substrates/400-499_advanced/substrato_435_orch_yin_yang/substrato_435_orch_yin_yang.py"
    module = load_module_from_path("substrato_435_orch_yin_yang", file_path)

    substrate = module.Substrato435OrchYinYang()
    report_path = substrate.canonize()

    assert os.path.exists(report_path)

    with open(report_path, "r") as f:
        data = json.load(f)

    assert "SEAL_435_ORCH_YIN_YANG" in data
    seal_data = data["SEAL_435_ORCH_YIN_YANG"]
    assert "Hash" in seal_data
    assert "Phi_C" in seal_data
    assert seal_data["Phi_C"] == 1.0000

    assert "Physical_Model" in seal_data
    phys_model = seal_data["Physical_Model"]
    assert phys_model["E_G"] == 6.27e-39
    assert phys_model["E_thermal"] == 4.28e-21
    assert phys_model["Lambda"] == 1.46e-18
    assert phys_model["N_critical"] == 907733

    assert "Decomposition" in seal_data
    decomp = seal_data["Decomposition"]
    assert decomp["Base"] == 0.2500
    assert decomp["Integration"] == 0.2000

    # Check that image was generated
    assert "Image_Path" in seal_data
    image_path = seal_data["Image_Path"]
    assert os.path.exists(image_path)

    # Clean up
    os.remove(report_path)
    # Be careful, if running as non-root the test might not have permission to delete from /mnt/agents/output
    # But for a basic check, we'll try to remove if we have access. If not, it's fine for the artifact to stay.
    try:
        os.remove(image_path)
    except PermissionError:
        pass
