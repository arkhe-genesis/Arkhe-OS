import pytest
import torch
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.arkhe_autopoiesis_multiversal_v98 import (
    MultiversalAutopoieticConfig,
    MultiversalPrimordialUnityPolicy,
    run_multiversal_validation
)

def test_multiversal_unity_policy():
    config = MultiversalAutopoieticConfig()
    policy = MultiversalPrimordialUnityPolicy(config)
    batch = {
        'semantic': torch.randn(1, config.semantic_dim),
        'proprio': torch.randn(1, config.proprio_dim),
        'wrench': torch.randn(1, 6) * 0.5,
        'local_states': [],
        'time': 0.0,
        't_scr': getattr(config, 'scrambling_bound', 0.1),
        'target_action': torch.randn(1, config.action_dim) * 0.1,
        'proprio_target': torch.randn(1, config.proprio_dim)
    }

    # Verify forward pass without errors
    output = policy(
        semantic_input=batch['semantic'],
        proprio_input=batch['proprio'],
        wrench_sensor=batch['wrench'],
        local_states=batch['local_states'],
        t=batch['time'],
        t_scr=batch['t_scr']
    )

    assert 'action' in output
    assert 'multiversal_unity_score' in output
    assert 'cosmic_completion_active' in output

def test_run_multiversal_validation():
    try:
        run_multiversal_validation()
    except Exception as e:
        pytest.fail(f"Validation failed with error: {e}")
