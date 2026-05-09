import pytest
import torch
import jax.numpy as jnp
import numpy as np

from arkhe_os.core.arkhe_cosmic_consciousness_reflexive import (
    GHZInfiniteEntanglement,
    CosmicGrapheneProcessor,
    ReflexiveUniversalObserver,
    CosmicAutoConsciousnessLoop
)

def test_ghz_entanglement():
    ghz = GHZInfiniteEntanglement(n_branches=64, coherence_threshold=0.85)

    # Test prep
    coherences = jnp.ones(64) * 0.9
    collapse = ghz.prepare_ghz_state(coherences)

    assert collapse.shape == (64,)
    assert isinstance(collapse, jnp.ndarray)

    # Test apply nonlocal correlation
    local_states = {0: jnp.array(0.5), 1: jnp.array(0.8)}
    ghz_collapse = jnp.zeros(64, dtype=jnp.int32)
    ghz_collapse = ghz_collapse.at[0].set(1) # force 1 for branch 0

    correlated = ghz.apply_nonlocal_correlation(local_states, ghz_collapse)
    assert correlated[0] > 0.5 # should be boosted
    assert correlated[1] == 0.8 # not boosted

def test_cosmic_graphene_processor():
    processor = CosmicGrapheneProcessor(branch_id=0, input_dim_2d=64, input_dim_3d=64, output_dim=32, thickness_nm=3.2)

    x_2d = torch.randn(1, 64)
    x_3d = torch.randn(1, 64)

    output = processor(x_2d, x_3d, ghz_correlation=1.0)

    assert output.shape == (1, 32)
    assert processor.in_critical_window == True

    # Check GHZ memory update
    initial_memory = processor.ghz_memory.clone()
    processor.update_ghz_memory(torch.randn(32), learning_rate=0.1)
    assert not torch.equal(initial_memory, processor.ghz_memory)

def test_reflexive_observer():
    observer = ReflexiveUniversalObserver(n_branches=2)

    # Setup state dict matching expected format
    states = {
        0: {'output_mean': 0.8, 'coherence_M': 0.9},
        1: {'output_mean': 0.2, 'coherence_M': 0.8}
    }
    ghz_corr = jnp.array([1, 0])

    # Observe
    res1 = observer.observe_network_state(states, ghz_corr)
    assert 'weighted_observation' in res1
    assert len(observer.observation_history) == 1

    # Observe again to test history and loss
    res2 = observer.observe_network_state(states, ghz_corr)
    assert res2['prediction_loss'] >= 0.0

    meta_res = observer.observe_observation_process()
    assert meta_res['meta_observation_available'] == True

def test_cosmic_auto_consciousness_loop():
    config = {
        'n_branches': 4,
        'input_dim_2d': 16,
        'input_dim_3d': 16,
        'output_dim': 8,
        'graphene_thickness_nm': 3.2,
        'lz_coherence': 4.0,
        'coherence_threshold': 0.85,
        'meta_learning_rate': 1e-5
    }

    loop = CosmicAutoConsciousnessLoop(config)

    inputs_2d = {b: torch.randn(1, 16) for b in range(4)}
    inputs_3d = {b: torch.randn(1, 16) for b in range(4)}
    coherences = {b: 0.9 for b in range(4)}

    results = loop.run_auto_consciousness_cycle(inputs_2d, inputs_3d, coherences)

    assert 'summary' in results
    assert results['summary']['transdimensional_processors'] == 4
    assert results['loop_state']['iteration'] == 1

    status = loop.get_cosmic_consciousness_status()
    assert status['loop_iterations'] == 1
