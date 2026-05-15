import pytest
import os
import sys
import tempfile
import asyncio
from cryptography.fernet import Fernet
import pandas as pd
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from audience.kantar_calibration import KantarCalibrationEngine
from security.federated_intel import FederatedThreatIntel, ThreatIndicator


class TestKantarCalibrationEngine:
    @pytest.fixture
    def sample_kantar_data(self):
        # Create a temporary CSV file with sample data
        data = {
            'timestamp': [time.time(), time.time(), time.time(), time.time()],
            'broadcaster': ['globo', 'globo', 'sbt', 'sbt'],
            'time_slot': ['prime_time', 'prime_time', 'morning', 'morning'],
            'genre': ['telenovela', 'news', 'entertainment', 'news'],
            'twitch_viewers': [10000, 5000, 2000, 1000],
            'kantar_rating_points': [15.0, 8.0, 4.0, 2.0]
        }
        df = pd.DataFrame(data)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        df.to_csv(temp_file.name, index=False)
        yield temp_file.name
        os.unlink(temp_file.name)

    def test_load_and_train(self, sample_kantar_data):
        engine = KantarCalibrationEngine()
        engine.load_kantar_data(sample_kantar_data)

        assert len(engine.data) == 4
        assert engine.data[0].broadcaster == 'globo'
        assert engine.data[0].kantar_viewers == int(15.0 * 750000)

        # Test default prediction before training
        pred_before = engine.predict_tv_viewers(10000, "prime_time", "telenovela")
        assert pred_before == 10000 * 120 # Default factor for prime_time is 120

        engine.train_models()

        # Models won't train with < 10 samples per segment, so it should fallback to defaults
        pred_after = engine.predict_tv_viewers(10000, "prime_time", "telenovela")
        assert pred_after == 10000 * 120

    def test_generate_report(self):
        engine = KantarCalibrationEngine()
        report = engine.generate_calibration_report()
        assert "calibration_timestamp" in report
        assert "canonical_seal" in report
        assert report["data_points"] == 0

class MockTemporalChain:
    def __init__(self):
        self.events = []

    async def anchor_event(self, event_type: str, payload: dict):
        self.events.append({"type": event_type, "payload": payload})


@pytest.mark.asyncio
class TestFederatedThreatIntel:
    @pytest.fixture
    def intel_engine(self):
        key = Fernet.generate_key()
        temporal = MockTemporalChain()
        engine = FederatedThreatIntel(
            broadcaster_id="globo",
            peers=["sbt", "record", "band"],
            encryption_key=key,
            temporal_chain=temporal
        )
        return engine

    async def test_report_and_query_threat(self, intel_engine):
        indicator = ThreatIndicator(
            indicator_type="ip",
            indicator_value="192.168.1.100",
            severity="high",
            first_seen=time.time(),
            last_seen=time.time(),
            confidence=0.9,
            source="ddos",
            affected_platforms=["twitch"],
            mitigation_applied=True,
            notes_encrypted="encrypted_notes_here"
        )

        # Report the threat
        hashed_ioc = await intel_engine.report_threat(indicator)

        # Check it's in local cache
        assert hashed_ioc in intel_engine.shared_iocs
        assert intel_engine.shared_iocs[hashed_ioc].severity == "high"

        # Query the threat
        correlation = await intel_engine.query_threat("192.168.1.100")

        assert correlation["ioc_hash"] == hashed_ioc
        assert correlation["local_match"] is True
        assert correlation["recommendation"] == "block"
        assert correlation["details"]["severity"] == "high"

        # Check stats
        stats = intel_engine.get_federated_stats()
        assert stats["iocs_reported"] == 1
        assert stats["correlation_queries"] == 1

        # Check temporal chain
        assert len(intel_engine.temporal.events) == 2 # report + query
        assert intel_engine.temporal.events[0]["type"] == "federated_intel_report"
        assert intel_engine.temporal.events[1]["type"] == "federated_intel_query"
