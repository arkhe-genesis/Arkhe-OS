import pytest
import importlib.util
import os
import sys

def test_substrato_438():
    script_path = "substrates/400-499_advanced/substrato_438_orch_agi/substrato_438_orch_agi.py"
    assert os.path.exists(script_path), f"File {script_path} not found"

    spec = importlib.util.spec_from_file_location("substrato_438_orch_agi", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Assertions based on module state if possible, though it's mainly a script
    assert hasattr(module, 'r438')
    assert hasattr(module, 's438')
    assert hasattr(module, 'time_vector')
    assert module.is_conscious == True or module.is_conscious == False # Check boolean
