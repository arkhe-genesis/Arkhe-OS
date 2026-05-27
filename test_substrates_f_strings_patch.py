import re

def test_617_f_strings():
    file_path = "substrates/617-QUANTUM-TELEPORT/substrato_617_quantum_teleport.py"
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    assert not re.search(r'\bf(["\'])', content), "f-strings found!"

def test_719_f_strings():
    import ast
    with open('substrates/s/719_glosa_240_metacognition/substrato_719_glosa_240_metacognition.py', 'r') as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):
        assert not isinstance(node, ast.JoinedStr)

def test_825_f_strings():
    import ast
    with open('substrates/t/825_parametric_memory_engine/substrato_825_parametric_memory_engine.py', 'r') as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):
        assert not isinstance(node, ast.JoinedStr)

def test_841_f_strings():
    import ast
    with open('substrates/t/841_web3_ontology_bridge/substrato_841_web3_ontology_bridge.py', 'r') as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):
        assert not isinstance(node, ast.JoinedStr)

def test_870_f_strings():
    import ast
    with open('substrates/t/870_blockchain_z_glm/substrato_870_blockchain_z_glm.py', 'r') as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):
        assert not isinstance(node, ast.JoinedStr)

def test_870_g_f_strings():
    import glob
    for filepath in glob.glob("substrates/t/870_g_arkhe_http_gateway/*.py"):
        with open(filepath, 'r') as f:
            content = f.read()
            assert "f\"" not in content, f"f-strings are strictly prohibited in the codebase. Found in {filepath}"

def test_pvac_f_strings_898_899_900():
    import os
    files_to_check = [
        "substrates/t/898_kolmogorov_weight/substrato_898.py",
        "substrates/t/899_lightclock_harmony/substrato_899.py",
        "substrates/t/900_peptide_saas/substrato_900.py",
    ]
    for file in files_to_check:
        with open(file, 'r') as f:
            content = f.read()
            assert 'f"' not in content, f"Found f-string in {file}"
            assert "f'" not in content, f"Found f-string in {file}"
