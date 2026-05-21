import os
import json
import importlib.util
import pytest

MODULE_PATH = "substrates/400-499_advanced/substrato_434_sfq_nv/substrato_434_sfq_nv.py"

def load_module_dynamically(path, name="substrato_434"):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_substrato_434_no_f_strings_or_non_ascii():
    with open(MODULE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Check for non-ASCII characters
    assert all(ord(c) < 128 for c in content), "O arquivo contem caracteres nao-ASCII."

    # Simple heuristic to check for f-strings
    import re
    assert not re.search(r'\bf[\'"]', content), "O arquivo contem f-strings, o que e proibido."

def test_substrato_434_report_generation():
    module = load_module_dynamically(MODULE_PATH)

    temp_path, report_data = module.generate_report()

    assert os.path.exists(temp_path), "O arquivo de relatorio JSON nao foi criado."

    with open(temp_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["phi_c"] == 0.9417, "Valor incorreto para phi_c"
    assert data["substrato"] == "434-SFQ-NV"
    assert "seal" in data, "Selo SHA3-256 ausente"
    assert data["status"] == "CANONIZADO"

    # Clean up the generated file
    os.remove(temp_path)
