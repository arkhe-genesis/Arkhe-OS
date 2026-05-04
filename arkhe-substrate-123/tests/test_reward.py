import pytest
from bandit.ceremony_reward import CeremonyReward

def test_ceremony_reward():
    reward_fn = CeremonyReward()

    # Test optimal case
    res1 = reward_fn.compute_with_components(latency_us=50.0, power_mw=30.0, epsilon=0.07)
    assert res1['mer_score'] == 1.0

    # Test penalty case
    res2 = reward_fn.compute_with_components(latency_us=50.0, power_mw=30.0, epsilon=0.01)
    assert res2['mer_score'] < 0.0
    assert res2['reward'] < res1['reward']
