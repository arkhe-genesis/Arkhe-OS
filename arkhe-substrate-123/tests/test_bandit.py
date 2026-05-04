import pytest
from bandit.kernel_variant import KernelVariant
from bandit.ceremony_reward import CeremonyReward
from bandit.ucb1_bandit import UCB1KernelBandit

def test_ucb1_bandit():
    v1 = KernelVariant(variant_id=1, ceremony="test", block_dim=128, tile_size=256, unroll_factor=4, shared_mem_bytes=1024, register_count=32, ptx_hash="hash1", verified_latency_us=100.0, verified_power_mw=50.0)
    v2 = KernelVariant(variant_id=2, ceremony="test", block_dim=256, tile_size=512, unroll_factor=8, shared_mem_bytes=2048, register_count=64, ptx_hash="hash2", verified_latency_us=80.0, verified_power_mw=60.0)
    variants = [v1, v2]
    reward_fn = CeremonyReward()
    bandit = UCB1KernelBandit(variants=variants, reward_fn=reward_fn, exploration_constant=2.0, warm_start_reward=0.5, warm_start_launches=2)

    assert len(bandit.variants) == 2
    selected_id = bandit.select_variant()
    assert selected_id in [1, 2]

    reward = bandit.update(selected_id, 90.0, 55.0, 0.07)
    assert 0 <= reward <= 1.0
