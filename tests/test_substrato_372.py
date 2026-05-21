import sys
import os
import importlib.util

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# Load module dynamically because of hyphens in directory name
module_name = 'substrato_372'
file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../substrates/300-399_foundations/substrato_372/substrato_372.py'))
spec = importlib.util.spec_from_file_location(module_name, file_path)
module = importlib.util.module_from_spec(spec)
sys.modules[module_name] = module
spec.loader.exec_module(module)

def test_phi_c_invariants():
    assert module.phi_c_372 > module.GHOST
    assert module.phi_c_372 > module.LOOPSEAL
    assert module.phi_c_372 < module.GAP_SOVEREIGN

def test_has_metrics():
    assert "contract_address" in module.humanity_proof_metrics
