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

def test_859_862_863_864_865_870_f_strings():
    import ast
    import glob
    import os
    files = [
        "substrates/t/855_hpc_environment_bridge/substrato_855_hpc_environment_bridge.py",
        "substrates/t/856_quantum_computing_bridge/substrato_856_quantum_computing_bridge.py",
        "substrates/t/857_neuromorphic_hardware_bridge/substrato_857_neuromorphic_hardware_bridge.py",
        "substrates/t/859_biological_computing_bridge/substrato_859_biological_computing_bridge.py",
        "substrates/t/860_consciousness_simulation_bridge/substrato_860_consciousness_simulation_bridge.py",
        "substrates/t/861_un_20_governance_bridge/substrato_861_un_20_governance_bridge.py",
        "substrates/t/862_polaritonic_computing_bridge/substrato_862_polaritonic_computing_bridge.py",
        "substrates/t/863_secops_guardian_bridge/substrato_863_secops_guardian_bridge.py",
        "substrates/t/864_eip8272_recent_roots_bridge/substrato_864_eip8272_recent_roots_bridge.py",
        "substrates/t/865_cohesion_engine/substrato_865_cohesion_engine.py",
        "substrates/t/870_blockchain_z_glm/substrato_870_blockchain_z_glm.py",
    ]
    for file in files:
        if not os.path.exists(file):
            continue
        with open(file, 'r') as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            assert not isinstance(node, ast.JoinedStr)

def test_245_f_strings():
    import ast
    import os
    file = "substrates/t/245_glosa/substrato_245_glosa.py"
    if os.path.exists(file):
        with open(file, 'r') as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            assert not isinstance(node, ast.JoinedStr)
