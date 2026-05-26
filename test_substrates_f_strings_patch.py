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
