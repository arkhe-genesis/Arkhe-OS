import pytest
import asyncio
from darkweb.proxy_config import get_production_proxies
from darkweb.multi_protocol_adapter import MultiProtocolAdapter, DarknetProtocol, CrawlResult
from darkweb.unified_shields import MultiProtocolTorVigil
from darkweb.cross_protocol_correlation import CrossProtocolCorrelationEngine

@pytest.fixture
def mock_dependencies():
    class DummyTemporal:
        async def anchor_event(self, event_type, details):
            return "seal_123"

    class DummyUnifiedDB:
        class DBEntry:
            def __init__(self, entry_type):
                self.entry_type = entry_type
        def query_by_perceptual_hash(self, hash_val):
            return [self.DBEntry("violation"), self.DBEntry("metadata")]

    return DummyTemporal(), DummyUnifiedDB()

@pytest.mark.asyncio
async def test_proxy_config():
    proxies = get_production_proxies()
    assert "tor" in proxies
    assert proxies["tor"].port == 9050
    assert proxies["i2p"].proxy_type == "http"

@pytest.mark.asyncio
async def test_multi_protocol_adapter():
    proxies = get_production_proxies()
    adapter = MultiProtocolAdapter(proxies)

    # Mock network call
    async def mock_fetch(self_instance, address, max_bytes=65536):
        return CrawlResult(b"fake content", 200, {})

    for prot in adapter.adapters:
        adapter.adapters[prot].fetch_page = mock_fetch.__get__(adapter.adapters[prot])

    result = await adapter.fetch_from_protocol(DarknetProtocol.TOR, "http://example.onion")
    assert result.status == 200

@pytest.mark.asyncio
async def test_correlation_engine(mock_dependencies):
    temporal, unified_db = mock_dependencies
    engine = CrossProtocolCorrelationEngine(unified_db, None, temporal, dp_epsilon=2.0)

    findings = [
        {"indicator_hash": "hash1234_full", "protocol": DarknetProtocol.TOR},
        {"indicator_hash": "hash1234_full2", "protocol": DarknetProtocol.I2P}
    ]

    campaigns = await engine.correlate(findings)
    assert len(campaigns) == 1
    assert campaigns[0].severity == "medium"
    assert campaigns[0].temporal_seal == "seal_123"

@pytest.mark.asyncio
async def test_multiprotocol_tor_vigil(mock_dependencies):
    temporal, _ = mock_dependencies

    proxies = get_production_proxies()
    adapter = MultiProtocolAdapter(proxies)

    async def mock_fetch(self_instance, address, max_bytes=65536):
        return CrawlResult(b"fake content", 200, {})

    adapter.adapters[DarknetProtocol.TOR].fetch_page = mock_fetch.__get__(adapter.adapters[DarknetProtocol.TOR])

    perceptual_db = {
        "hash1": {"confidence": 0.99, "type": "csam", "source": "darknet_example"}
    }

    shield = MultiProtocolTorVigil(adapter, None, None, None, temporal, perceptual_db)

    async def mock_extract(page):
        return ["hash1"]

    shield._extract_image_perceptual_hashes = mock_extract

    findings = await shield.monitor_service(DarknetProtocol.TOR, "http://example.onion")
    assert len(findings) == 1
    assert findings[0].violation_type == "csam"
    assert findings[0].temporal_seal == "seal_123"
