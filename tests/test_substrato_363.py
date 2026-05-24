import pytest
import sys
import os

sys.path.insert(0, os.path.abspath('substrates/300-399_foundations/substrato_363'))
from substrato_363_exp import SafeCoreSDKv3Exp, GHOST, LOOPSEAL, GAP_SOVEREIGN

def test_safe_core_sdk_init():
    sdk = SafeCoreSDKv3Exp()
    assert len(sdk.integrations) == len(sdk.PARTNERS)
    assert sdk.integrations["kimi"]["tier"] == 1
    assert sdk.integrations["alibaba"]["tier"] == 3

def test_authenticate_partner():
    sdk = SafeCoreSDKv3Exp()

    # Test valid authentication
    res = sdk.authenticate_partner("kimi", "0000-0000-0000-0000", GHOST + 0.2)
    assert res["status"] == "authenticated"
    assert "session_id" in res

    # Test rejected authentication (low humility for tier 1)
    res2 = sdk.authenticate_partner("anthropic", "1111-1111-1111-1111", GHOST)
    assert res2["status"] == "rejected"

def test_compute_workload():
    sdk = SafeCoreSDKv3Exp()
    auth_res = sdk.authenticate_partner("nvidia", "0000-0000-0000-0001", GHOST + 0.2)

    res = sdk.compute_workload("nvidia", "training", 0.5, "hash123", auth_res["session_id"])
    assert res["status"] == "computed"
    assert res["phi_c"] >= GHOST
    assert res["phi_c"] <= GAP_SOVEREIGN

def test_cross_substrate_test():
    sdk = SafeCoreSDKv3Exp()

    res = sdk.cross_substrate_test("kimi", "alibaba", "bridge_test")
    assert res["status"] in ["passed", "failed"]
    assert "seal" in res

def test_get_sdk_statistics():
    sdk = SafeCoreSDKv3Exp()
    stats = sdk.get_sdk_statistics()

    assert stats["total_partners"] > 50
    assert "tier_stats" in stats
