import pytest
from substrato_9033_arkhe_tv import Substrato9033ArkheTV

def test_substrato_9033_pipeline():
    tv = Substrato9033ArkheTV()
    result = tv.run_full_pipeline_mock()

    assert "coherence" in result
    assert result["coherence"] > 0
    assert result["status"] == "OK"
    assert "event_hash" in result
    assert "signal_status" in result
    assert result["signal_status"]["overall_status"] == "OK"
    assert result["signal_status"]["cnr_ok"] is True
    assert result["signal_status"]["mer_ok"] is True
    assert result["signal_status"]["txid_ok"] is True

def test_physical_layer_validator():
    tv = Substrato9033ArkheTV()
    val = tv.physical_validator

    assert val.check_cnr(25.0, 1e-9) is True
    assert val.check_cnr(20.0, 1e-9) is False

    assert val.check_mer(32.0) is True
    assert val.check_mer(28.0) is False

    assert val.check_mimo("2x2") is True
    assert val.check_mimo("1x1") is False

    assert val.check_ldm({"core_layer": 1, "enhanced_layer": 2}) is True
    assert val.check_ldm({"core_layer": 1}) is False

    assert val.check_txid("TX_01") is True
    assert val.check_txid("") is False

def test_mcp_tools():
    tv = Substrato9033ArkheTV()
    mcp = tv.mcp_server

    content_res = mcp.call_tool("tv3_validate_content", {"content_id": "seg_123"})
    assert content_res["status"] == "Approved"

    anchor_res = mcp.call_tool("tv3_anchor_event", {"event_type": "phi_c_alert", "segment_hash": "hash123"})
    assert anchor_res["status"] == "Anchored"
    assert "tx_hash" in anchor_res

def test_phi_c_monitor():
    tv = Substrato9033ArkheTV()
    monitor = tv.phi_monitor

    # Perfect metrics
    metrics = {"cnr": 40.0, "mer": 40.0, "ber": 0.0}
    coh = monitor.compute_coherence(metrics)
    assert coh == 1.0
    assert monitor.alert_threshold(coh) == "OK"

    # Critical metrics
    metrics_crit = {"cnr": 10.0, "mer": 10.0, "ber": 0.9}
    coh_crit = monitor.compute_coherence(metrics_crit)
    assert coh_crit < 0.6
    assert monitor.alert_threshold(coh_crit) == "Crítico"
