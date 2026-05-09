import pytest
import math
from core.hardware.ucb1_bandit import UCB1KernelBandit, KernelVariant, CeremonyReward

def generate_mock_variants():
    return [
        KernelVariant(variant_id=1, ceremony="test", block_dim=128, tile_size=256, unroll_factor=4, shared_mem_bytes=1024, register_count=32, ptx_hash="hash1", verified_latency_us=100.0, verified_power_mw=50.0),
        KernelVariant(variant_id=2, ceremony="test", block_dim=256, tile_size=512, unroll_factor=8, shared_mem_bytes=2048, register_count=64, ptx_hash="hash2", verified_latency_us=200.0, verified_power_mw=100.0),
        KernelVariant(variant_id=3, ceremony="test", block_dim=512, tile_size=1024, unroll_factor=16, shared_mem_bytes=4096, register_count=128, ptx_hash="hash3", verified_latency_us=300.0, verified_power_mw=150.0)
    ]

def test_ucb1_bandit_initialization():
    variants = generate_mock_variants()
    reward_fn = CeremonyReward()
    bandit = UCB1KernelBandit(variants=variants, reward_fn=reward_fn, warm_start_launches=0)
    assert len(bandit.variants) == 3
    assert bandit.total_launches == 0

def test_ucb1_bandit_exploration():
    variants = generate_mock_variants()
    reward_fn = CeremonyReward()
    bandit = UCB1KernelBandit(variants=variants, reward_fn=reward_fn, warm_start_launches=0)
    # First selections should force exploration
    selections = set()
    for _ in range(3):
        kid = bandit.select_variant()
        selections.add(kid)
        bandit.update(kid, 100.0, 50.0, 0.07)

    # Actually, UCB1 will pull arms sequentially if they have 0 pulls, because it forces exploration
    # But note that they all have total_launches = 0 initially so the first one might get picked multiple times if we don't update them, but we do update.
    # Wait, the first arm picked will have pulls=1, the others 0. The next `select_variant` will see others with 0 and pick one of them.
    assert len(selections) == 3
    assert bandit.total_launches == 3

def test_ucb1_bandit_exploitation():
    variants = generate_mock_variants()
    reward_fn = CeremonyReward()
    bandit = UCB1KernelBandit(variants=variants, reward_fn=reward_fn, warm_start_launches=0)

    # Manually pull each arm once to get past the 0-pull check
    for kid in [1, 2, 3]:
        bandit.select_variant() # It will pick the first unpulled one
        if kid == 1:
            # Optimal telemetry (epsilon exactly at target)
            bandit.update(kid, 100.0, 50.0, 0.07)
        else:
            # Suboptimal telemetry
            bandit.update(kid, 500.0, 150.0, 0.07)

    # Next selection should heavily favor 1 because of high reward
    assert bandit.select_variant() == 1
