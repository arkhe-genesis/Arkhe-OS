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

def test_add_laplace_noise():
    correlator = FederatedThreatCorrelator()
    true_count = 100

    # Epsilon alto => Menos ruído
    epsilon_high = 10.0
    values_high = [correlator._add_laplace_noise(true_count, epsilon_high) for _ in range(100)]
    variance_high = sum((x - true_count)**2 for x in values_high) / len(values_high)

    # Epsilon baixo => Mais ruído
    epsilon_low = 0.1
    values_low = [correlator._add_laplace_noise(true_count, epsilon_low) for _ in range(100)]
    variance_low = sum((x - true_count)**2 for x in values_low) / len(values_low)

    # Variância com epsilon baixo deve ser maior
    assert variance_low > variance_high

@pytest.mark.asyncio
async def test_cross_org_correlation_3_partners(mock_phi_bus):
    correlator = FederatedThreatCorrelator(phi_bus=mock_phi_bus)
    p1, p2, p3 = PARTNER_ORGS[0], PARTNER_ORGS[1], PARTNER_ORGS[2]

    target_ip = "192.168.1.100"

    # Parceiro 1
    await correlator.ingest_threat(p1, ThreatIndicator(
        ioc_id="ioc_1", ioc_type="ip", value=target_ip, severity=5, confidence=0.7,
        source_org=p1.org_id, first_seen=time.time(), last_seen=time.time()
    ))
    assert len(correlator._correlations) == 0

    # Parceiro 2
    await correlator.ingest_threat(p2, ThreatIndicator(
        ioc_id="ioc_2", ioc_type="ip", value=target_ip, severity=6, confidence=0.8,
        source_org=p2.org_id, first_seen=time.time(), last_seen=time.time()
    ))
    assert len(correlator._correlations) == 1
    assert len(correlator._correlations[0]["sources"]) == 2

    # Parceiro 3
    await correlator.ingest_threat(p3, ThreatIndicator(
        ioc_id="ioc_3", ioc_type="ip", value=target_ip, severity=8, confidence=0.9,
        source_org=p3.org_id, first_seen=time.time(), last_seen=time.time()
    ))
    assert len(correlator._correlations) == 2
    assert len(correlator._correlations[1]["sources"]) == 2  # The second correlation event also links with the existing one
    assert correlator._correlations[1]["severity_max"] == 8
