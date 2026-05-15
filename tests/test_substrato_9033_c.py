#!/usr/bin/env python3
"""
Testes unitários e de integração para Substrato 9033-C: Audience Bridge
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from arkhe_tv.audience_bridge.aggregator import AudienceAggregator, AudienceSnapshot
from arkhe_tv.audience_bridge.projection import AudienceProjection
from arkhe_tv.audience_bridge.api import app, set_aggregator

class MockPhiCMonitor:
    def get_mesh_coherence(self):
        return 0.99

class MockTemporalChainAnchor:
    async def anchor_event(self, event_type, data):
        return "mock_temporal_seal_abc123"

@pytest.fixture
def aggregator():
    return AudienceAggregator(
        twitch_client_id="mock_id",
        twitch_token="mock_token",
        yt_api_key="mock_yt",
        temporal_chain=MockTemporalChainAnchor(),
        phi_bus=MockPhiCMonitor()
    )

@pytest.fixture
def client(aggregator):
    set_aggregator(aggregator)
    return TestClient(app)

@pytest.mark.asyncio
async def test_aggregator_initialization(aggregator):
    assert aggregator.twitch_client_id == "mock_id"
    assert "globo" in aggregator.BROADCASTER_MAPPINGS

@pytest.mark.asyncio
async def test_aggregator_empty_get_audience(aggregator):
    snapshot = await aggregator.get_audience("globo")
    assert isinstance(snapshot, AudienceSnapshot)
    assert snapshot.broadcaster_id == "globo"
    assert snapshot.total_viewers == 0
    assert snapshot.phi_c_coherence == 0.99
    assert snapshot.temporal_seal == "mock_temporal_seal_abc123"

def test_audience_projection():
    proj = AudienceProjection()
    # Test prime time
    factor_prime = proj.get_conversion_factor(20)
    assert factor_prime == 100.0

    # Test morning
    factor_morning = proj.get_conversion_factor(8)
    assert factor_morning == 40.0

    # Projection calculations (simulate 8AM timestamp)
    res = proj.project_tv_audience(5000, 1715712000) # Assuming the timestamp evaluates to some hour.
    # The datetime will be locale specific but logic stands.
    assert "projected_tv_viewers" in res

def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "audience-bridge", "version": "9033-C"}

def test_get_simple_audience(client):
    response = client.get("/api/v1/audience/globo/simple")
    assert response.status_code == 200
    data = response.json()
    assert "v" in data
    assert "tw" in data
    assert data["v"] == 0

def test_get_broadcaster_audience(client):
    response = client.get("/api/v1/audience/sbt")
    assert response.status_code == 200
    data = response.json()
    assert data["broadcaster_id"] == "sbt"
    assert data["total_viewers"] == 0
    assert data["phi_c_coherence"] == 0.99
    assert data["temporal_seal"] == "mock_temporal_seal_abc123"

def test_get_all_audiences(client):
    response = client.get("/api/v1/audience")
    assert response.status_code == 200
    data = response.json()
    assert "broadcasters" in data
    assert "globo" in data["broadcasters"]
    assert "sbt" in data["broadcasters"]
