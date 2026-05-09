import pytest
import sys
import os

# Ensure the root directory is in the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Fallback test if torch is not present
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

if TORCH_AVAILABLE:
    from arkhe_infinity.model import (
        ARKHEInfinity,
        ARKHEInfinityConfig,
        MissionGraph
    )

def test_arkhe_infinity_instantiation_and_forward():
    if not TORCH_AVAILABLE:
        pytest.skip("PyTorch not available, skipping full instantiation test.")

    # Instantiate with default config
    config = ARKHEInfinityConfig()
    model = ARKHEInfinity(config)

    # Verify it is instantiated correctly
    assert model is not None
    assert model.config == config

    # Create dummy inputs
    input_forms = {
        0: torch.zeros((1, 24576)), # mock input matching expected shape
        1: torch.zeros((1, 24576))
    }
    mission_graph = MissionGraph()
    privacy_budget = {'remaining_epsilon': 1.0}

    # Call forward pass
    output = model(
        input_forms=input_forms,
        mission_graph=mission_graph,
        privacy_budget=privacy_budget
    )

    # Verify basic output properties
    assert output is not None
    assert output.status in ["OK", "PRIVACY_BUDGET_EXHAUSTED"]

def test_arkhe_infinity_syntax():
    # Attempt to import to check syntax if not already caught
    try:
        from arkhe_infinity.model import ARKHEInfinity
        assert True
    except ImportError as e:
        if "torch" not in str(e).lower():
            raise

if __name__ == '__main__':
    pytest.main([__file__])
