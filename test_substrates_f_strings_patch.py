import re

def test_617_f_strings():
    file_path = "substrates/617-QUANTUM-TELEPORT/substrato_617_quantum_teleport.py"
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    assert not re.search(r'\bf(["\'])', content), "f-strings found!"
