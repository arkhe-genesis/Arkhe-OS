import pytest
import asyncio
from substrate_250.siem.siem_forwarder import SIEMForwarder, SIEMConfig, ArkheEvent, EventSeverity, SIEMTarget
from substrate_250.ml.config_optimizer import MLConfigOptimizer, OptimizationGoal
from substrate_250.gpo.multi_domain_engine import MultiDomainGPOEngine, DomainTrustType

@pytest.mark.asyncio
async def test_siem_config_and_filtering():
    config = SIEMConfig(
        splunk_hec_url="https://mock-splunk:8088",
        splunk_hec_token="mock-token",
        targets=SIEMTarget.SPLUNK_HEC,
        min_severity=EventSeverity.HIGH,
        anchor_to_temporal_chain=False
    )
    forwarder = SIEMForwarder(config)

    # Event should be filtered out due to low severity
    low_sev_event = ArkheEvent(
        event_id=3003,
        event_name="ModuleLoadStateChanged",
        severity=EventSeverity.LOW,
        timestamp=1000.0,
        registry_path=None,
        value_name=None,
        old_value=None,
        new_value=None,
        phi_c_before=None,
        phi_c_after=None,
        temporal_seal=None,
        constitutional_check="not_applicable",
        source_host="test-host",
        user_context="SYSTEM",
        raw_message="test"
    )

    success = await forwarder.forward_event(low_sev_event)
    assert success is True # Filtering out is considered success
    stats = forwarder.get_stats()
    assert stats["forwarded_splunk"] == 0

@pytest.mark.asyncio
async def test_ml_optimizer_initialization():
    optimizer = MLConfigOptimizer(goal=OptimizationGoal.MAXIMIZE_PHI_C)
    assert optimizer.goal == OptimizationGoal.MAXIMIZE_PHI_C

    # Generate heuristic recommendation
    recs = optimizer.generate_recommendations(top_n=1)
    assert len(recs) <= 1
    if recs:
        assert recs[0].risk_level in ["low", "medium", "high"]

@pytest.mark.asyncio
async def test_gpo_engine_initialization():
    engine = MultiDomainGPOEngine("arkhe.org", "ldap://mock", "user", "pass")
    domains = await engine.discover_forest_domains()
    assert len(domains) > 0
    assert domains[0].domain_name == "production.arkhe.org"

    policy = engine.create_cross_domain_policy(
        gpo_name="Test-Policy",
        scope_domains=["production.arkhe.org"],
        arkhe_values={"Network/BusPort": 8443}
    )
    assert policy.gpo_name == "Test-Policy"
    assert "production.arkhe.org" in policy.scope_domains
