import pytest
import subprocess
import os

def test_substrato_813_f_strings():
    with open('substrates/t/813_arkhe_sys_visualization/substrato_813_arkhe_sys_visualization.py', 'r') as f:
        content = f.read()
    assert 'f"' not in content
    assert "f'" not in content

def test_substrato_813_execution():
    result = subprocess.run(['python', 'substrates/t/813_arkhe_sys_visualization/substrato_813_arkhe_sys_visualization.py'], capture_output=True, text=True)
    assert result.returncode == 0
    assert "Substrato 813 gerado com sucesso!" in result.stdout
