import os
import json
import importlib.util

def test_substrato_v_omega_ai_canonize():
    module_name = "substrato_v_omega_ai"
    file_path = "substrates/400-499_advanced/substrato_v_omega_ai/substrato_v_omega_ai.py"

    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    substrate = module.SubstratoVOmegaAi()
    path = substrate.canonize()

    assert os.path.exists(path)

    with open(path, 'r') as f:
        data = json.load(f)

    assert "Title" in data
    assert "ARKHE OS v" in data["Title"]
    assert "Content" in data
    assert "0.9944" in data["Content"]

    # Ensure no f-strings or non-ASCII characters in source code
    with open(file_path, 'r', encoding='ascii') as f:
        code = f.read()
        assert "f\"" not in code
        assert "f'" not in code

    os.remove(path)
