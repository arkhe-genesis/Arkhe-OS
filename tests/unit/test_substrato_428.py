import os
import json
import importlib.util
import pytest

MODULE_PATH = "substrates/400-499_advanced/substrato_428_blue_clique/substrato_428_blue_clique.py"

def load_module_dynamically(path, name="substrato_428"):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_substrato_428_no_f_strings_or_non_ascii():
    with open(MODULE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Check for non-ASCII characters
    assert all(ord(c) < 128 for c in content), "O arquivo contem caracteres nao-ASCII."

    # Simple heuristic to check for f-strings
    # Matches typical f-string usage like f"..." or f'...'
    import re
    assert not re.search(r'\bf[\'"]', content), "O arquivo contem f-strings, o que e proibido."

def test_substrato_428_report_generation():
    module = load_module_dynamically(MODULE_PATH)

    temp_path, report_data = module.generate_report()

    assert os.path.exists(temp_path), "O arquivo de relatorio JSON nao foi criado."

    with open(temp_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["phi_c"] == 0.7629, "Valor incorreto para phi_c"
    assert data["substrato"] == "428-BLUE-CLIQUE"
    assert "seal" in data, "Selo SHA3-256 ausente"
    assert data["status"] == "CANONIZADO"

    # Clean up the generated file
    os.remove(temp_path)
