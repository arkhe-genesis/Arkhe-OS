import pytest
import torch
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.arkhe_neuromorphic_embodied_v96 import (
    NeuromorphicPolicyConfig,
    NeuromorphicEmbodiedPolicy,
    EventDrivenFiLM,
    LocalReflexConsensus,
    SurrogateLIFNeuron
)

def test_film_event_driven():
    film = EventDrivenFiLM(input_dim=8, context_dim=16, threshold=0.1)

    # Test with low error (no update)
    z_sem = torch.ones(1, 8)
    h_context = torch.ones(1, 16)
    proprio_error = torch.tensor([0.05])
    t = 0.0

    z_mod_low_error = film(z_sem, h_context, proprio_error, t)

    # Test with high error (update)
    proprio_error_high = torch.tensor([0.5])
    z_mod_high_error = film(z_sem, h_context, proprio_error_high, t)

    # The cache should be updated and therefore the output should be different
    # Since we initialize cached tensors to zeros and ones, the first high error will update them
    assert not torch.allclose(z_mod_low_error, z_mod_high_error)

def test_local_reflex_consensus():
    reflex = LocalReflexConsensus(n_local_neighbors=2, reflex_threshold=4.0)

    wrench_normal = torch.randn(6) * 0.5
    wrench_collision = torch.randn(6) * 5.0

    assert reflex.detect_collision(wrench_normal) == 0.0
    assert reflex.detect_collision(wrench_collision) == 1.0

    local_states = [{'wrench': torch.randn(6) * 5.0}, {'wrench': torch.randn(6) * 5.0}]
    consensus = reflex.compute_local_consensus(local_states)
    assert consensus > 0.0

def test_neuromorphic_policy():
    config = NeuromorphicPolicyConfig(
        semantic_dim=32,
        context_dim=16,
        action_dim=6,
        proprio_dim=12
    )
    policy = NeuromorphicEmbodiedPolicy(config)

    batch = {
        'semantic': torch.randn(1, config.semantic_dim),
        'proprio': torch.randn(1, config.proprio_dim),
        'wrench': torch.randn(1, 6) * 0.5,
        'local_states': [],
        'time': 0.0,
        't_scr': config.scrambling_bound,
        'target_action': torch.randn(1, config.action_dim),
        'proprio_target': torch.randn(1, config.proprio_dim)
    }

    output = policy(
        semantic_input=batch['semantic'],
        proprio_input=batch['proprio'],
        wrench_sensor=batch['wrench'],
        local_states=batch['local_states'],
        t=batch['time'],
        t_scr=batch['t_scr']
    )

    assert 'action' in output
    assert 'action_spikes' in output
    assert 'metrics' in output

    assert output['action'].shape == (1, config.action_dim)

    # Test training step
    metrics = policy.training_step(batch)
    assert 'loss' in metrics
    assert 'action_loss' in metrics
