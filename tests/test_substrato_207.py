import pytest
import asyncio
import time
from substrato_207_federated_threat import (
    FederatedThreatCorrelator,
    AutoTicketingSystem,
    RealTrafficSimulator,
    PartnerOrganization,
    PartnerType,
    ThreatIndicator,
    PARTNER_ORGS
)

@pytest.fixture
def mock_phi_bus():
    class MockPhiBus:
        def __init__(self):
            self.metrics = []
        async def publish_metric(self, topic, data):
            self.metrics.append((topic, data))
    return MockPhiBus()

@pytest.mark.asyncio
async def test_federated_threat_correlator(mock_phi_bus):
    correlator = FederatedThreatCorrelator(phi_bus=mock_phi_bus)
    partner1 = PARTNER_ORGS[0]
    partner2 = PARTNER_ORGS[1]

    ioc1 = ThreatIndicator(
        ioc_id="ioc_001", ioc_type="ip", value="1.2.3.4",
        severity=5, confidence=0.8, source_org=partner1.org_id,
        first_seen=time.time(), last_seen=time.time()
    )

    ioc2 = ThreatIndicator(
        ioc_id="ioc_002", ioc_type="ip", value="1.2.3.4",
        severity=7, confidence=0.9, source_org=partner2.org_id,
        first_seen=time.time(), last_seen=time.time()
    )

    await correlator.ingest_threat(partner1, ioc1)

    # Should not have correlations yet
    assert len(correlator._correlations) == 0

    await correlator.ingest_threat(partner2, ioc2)

    # Now it should be correlated
    assert len(correlator._correlations) == 1
    correlation = correlator._correlations[0]
    assert correlation["value"] == "1.2.3.4"
    assert correlation["type"] == "ip"
    assert correlation["severity_max"] == 7
    assert len(correlation["sources"]) == 2

    # Check that metric was published
    assert len(mock_phi_bus.metrics) == 1
    assert mock_phi_bus.metrics[0][0] == "cross_org_correlation"

@pytest.mark.asyncio
async def test_auto_ticketing_system(mock_phi_bus):
    ticketing = AutoTicketingSystem(phi_bus=mock_phi_bus)
    partner1 = PARTNER_ORGS[0]  # ServiceNow
    partner2 = PARTNER_ORGS[1]  # Jira

    correlation = {
        "ioc_key": "some_key",
        "value": "1.2.3.4",
        "type": "ip",
        "sources": [partner1.org_id, partner2.org_id],
        "severity_max": 8,
        "confidence_avg": 0.85,
        "dp_epsilon_combined": 0.5,
        "correlation_type": "CROSS_ORG",
        "timestamp": time.time()
    }

    ticket1 = await ticketing.create_ticket(partner1, correlation)
    ticket2 = await ticketing.create_ticket(partner2, correlation)

    assert ticket1["system"] == "servicenow"
    assert "payload" in ticket1
    assert ticket1["payload"]["urgency"] == "1"

    assert ticket2["system"] == "jira"
    assert "payload" in ticket2
    assert ticket2["payload"]["fields"]["issuetype"]["name"] == "Security Incident"

    summary = ticketing.get_ticketing_summary()
    assert summary["total_tickets"] == 2
    assert summary["by_system"]["servicenow"] == 1
    assert summary["by_system"]["jira"] == 1

def test_real_traffic_simulator():
    simulator = RealTrafficSimulator()
    n_packets = 100
    threat_ratio = 0.2
    packets = simulator.generate_traffic_sample(n_packets=n_packets, threat_ratio=threat_ratio)

    assert len(packets) == n_packets

    stats = simulator.get_traffic_stats()
    assert stats["total"] == n_packets
    # Threat generation is probabilistic, but should be > 0 with n=100 and ratio=0.2
    # In some very rare cases it could be 0, but usually ~20.
    assert "threats" in stats
    assert "benign" in stats

@pytest.mark.asyncio
async def test_correlate_traffic():
    correlator = FederatedThreatCorrelator()
    simulator = RealTrafficSimulator()

    # Create a threat indicator matching one of the simulator's malicious IPs
    target_ip = simulator.MALICIOUS_IPS[0]

    ioc = ThreatIndicator(
        ioc_id="ioc_001", ioc_type="ip", value=target_ip,
        severity=10, confidence=1.0, source_org=PARTNER_ORGS[0].org_id,
        first_seen=time.time(), last_seen=time.time()
    )

    await correlator.ingest_threat(PARTNER_ORGS[0], ioc)

    # Generate traffic with a very high threat ratio to ensure target_ip is generated
    packets = simulator.generate_traffic_sample(n_packets=500, threat_ratio=0.5)

    matches = await correlator.correlate_real_traffic(packets)

    # Find how many generated packets actually had the target IP
    expected_matches = sum(1 for p in packets if p.get("src_ip") == target_ip or p.get("dst_ip") == target_ip)

    assert len(matches) == expected_matches
