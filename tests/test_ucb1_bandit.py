import pytest
from core.hardware.ucb1_bandit import KernelVariant, KernelZoo, CeremonyReward, UCB1KernelBandit

def test_kernel_zoo():
    zoo = KernelZoo("pdi_computation")
    var = KernelVariant(
        variant_id=0,
        ceremony="pdi_computation",
        block_dim=128,
        tile_size=0,
        unroll_factor=8,
        shared_mem_bytes=2048,
        register_count=48,
        ptx_hash="abc",
        verified_latency_us=500.0,
        verified_power_mw=150.0
    )
    zoo.add_variant(var)
    assert zoo.num_variants() == 1
    assert zoo.get_variant(0) == var
    assert zoo.all_ids() == [0]

def test_ceremony_reward():
    reward_fn = CeremonyReward()
    r = reward_fn.compute(latency_us=100.0, power_mw=50.0, epsilon=0.07)
    assert r > 0.8

    r_bad = reward_fn.compute(latency_us=100.0, power_mw=50.0, epsilon=0.01)
    assert r_bad < r

def test_ucb1_bandit():
    zoo = KernelZoo("pdi_computation")
    for i in range(3):
        zoo.add_variant(KernelVariant(
            variant_id=i,
            ceremony="pdi_computation",
            block_dim=128,
            tile_size=0,
            unroll_factor=8,
            shared_mem_bytes=2048,
            register_count=48,
            ptx_hash="abc",
            verified_latency_us=500.0,
            verified_power_mw=150.0
        ))

    reward_fn = CeremonyReward()
    bandit = UCB1KernelBandit(zoo, reward_fn)

    selected_id = bandit.select_variant(total_launches=10)
    assert selected_id in [0, 1, 2]

    bandit.update(variant_id=0, latency_us=100.0, power_mw=50.0, epsilon=0.07)
    var = zoo.get_variant(0)
    assert var.total_launches == 3  # 2 warm start + 1

    # Test fallback by setting all bad epsilon
    bandit.update(variant_id=0, latency_us=100.0, power_mw=50.0, epsilon=0.01)
    bandit.update(variant_id=1, latency_us=100.0, power_mw=50.0, epsilon=0.01)
    bandit.update(variant_id=2, latency_us=100.0, power_mw=50.0, epsilon=0.01)
    fallback_id = bandit.select_variant(total_launches=15)
    assert fallback_id is not None
