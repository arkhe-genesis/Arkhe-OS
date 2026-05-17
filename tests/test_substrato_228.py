import pytest
import asyncio
import hashlib
import time
import pandas as pd
from unittest.mock import AsyncMock, MagicMock

from rights_shield.creator_production_portal import CreatorProductionPortal, CreatorVerificationStatus
from legal.judicial_evidence_framework import JudicialEvidenceFramework, CourtJurisdiction
from platforms.official_api_integrator import OfficialAPIIntegrator, PlatformAPI
from ml.continuous_deepfake_retraining import ContinuousRetrainingPipeline

# --- Mocks ---
class MockTemporalChain:
    async def anchor_event(self, event_type, data):
        return f"mock_seal_{event_type}_{int(time.time())}"

class MockHSM:
    async def sign_data(self, data, context):
        return {"signature_hex": "mock_sig_123"}

class MockDetector:
    async def generate_fingerprint(self, data):
        return "mock_fingerprint_abc"

class MockTracker:
    async def embed_watermark(self, data, context):
        return "mock_watermark_xyz"

# --- Testes Creator Portal ---
@pytest.mark.asyncio
async def test_creator_onboarding():
    portal = CreatorProductionPortal(
        temporal_chain=MockTemporalChain(),
        hsm_signer=MockHSM()
    )

    data = {
        "orcid": "orcid:1234",
        "display_name": "Test Creator",
        "email": "test@example.com",
        "tier": "premium"
    }

    profile = await portal.onboard_creator(data, b"proof", "biohash")

    assert profile.display_name == "Test Creator"
    assert profile.verification_status == CreatorVerificationStatus.PENDING
    assert profile.protection_tier == "premium"
    assert "mock_seal" in profile.temporal_seal

@pytest.mark.asyncio
async def test_register_content():
    portal = CreatorProductionPortal(
        temporal_chain=MockTemporalChain(),
        hsm_signer=MockHSM(),
        detector=MockDetector(),
        tracker=MockTracker()
    )

    # Onboard e aprova
    data = {"orcid": "orcid:1234", "display_name": "Test Creator", "email": "test@example.com"}
    profile = await portal.onboard_creator(data, b"proof", "biohash")
    profile.verification_status = CreatorVerificationStatus.VERIFIED

    content = await portal.register_content(
        creator_id=profile.creator_id,
        content_data=b"image_data",
        metadata={"policy": "no_use"}
    )

    assert content.creator_id == profile.creator_id
    assert content.fingerprint == "mock_fingerprint_abc"
    assert content.watermark_payload == "mock_watermark_xyz"
    assert len(content.platforms_monitored) == 4 # default standard

# --- Testes Judicial Framework ---
@pytest.mark.asyncio
async def test_judicial_evidence_preparation():
    framework = JudicialEvidenceFramework(
        temporal_chain=MockTemporalChain(),
        hsm_signer=MockHSM()
    )

    framework.register_expert_partner(
        "EXP-001", CourtJurisdiction.BRAZIL_FEDERAL, "Forensics", {}
    )

    evidence = await framework.prepare_judicial_evidence(
        case_details={"case_reference": "REF-123"},
        temporal_seals=["seal1", "seal2"],
        chain_of_custody_data=[{"step": 1}],
        jurisdiction=CourtJurisdiction.BRAZIL_FEDERAL
    )

    assert evidence.case_reference == "REF-123"
    assert evidence.jurisdiction == CourtJurisdiction.BRAZIL_FEDERAL
    assert evidence.expert_affidavit is not None
    assert "EXP-001" in evidence.expert_affidavit
    assert len(evidence.pqc_signatures) == 1

# --- Testes Platform API ---
@pytest.mark.asyncio
async def test_platform_takedown_submission(monkeypatch):
    api = OfficialAPIIntegrator(temporal_chain=MockTemporalChain())

    # Mock aiohttp para teste
    class MockResponse:
        status = 201
        async def json(self):
            return {"id": "MOCK-123456"}
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    class MockClientSession:
        def post(self, url, **kwargs):
            return MockResponse()
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    monkeypatch.setattr("aiohttp.ClientSession", MockClientSession)

    req = await api.submit_takedown(
        platform=PlatformAPI.YOUTUBE_CONTENT_ID,
        content_hash="hash123",
        violation_url="https://youtube.com/watch?v=123",
        claimant_id="claimant1",
        evidence_seals=["seal1"],
        legal_basis="DMCA"
    )

    assert req.platform == PlatformAPI.YOUTUBE_CONTENT_ID
    assert req.content_hash == "hash123"
    assert req.status in ["processing", "pending"]
    assert req.platform_reference.startswith("MOCK")

# --- Testes Continuous Retraining ---
@pytest.mark.asyncio
async def test_retraining_pipeline(monkeypatch):
    pipeline = ContinuousRetrainingPipeline(temporal_chain=MockTemporalChain())

    # Gerar dados sintéticos para teste
    data = await pipeline.collect_new_training_data(days_back=1)

    assert not data.empty
    assert len(data) > 0
    assert "is_deepfake" in data.columns

    # Para o teste, mockamos _evaluate_ab_test para não esperar 24h
    import asyncio

    async def mock_evaluate_ab_test(*args, **kwargs):
        pass
    monkeypatch.setattr(pipeline, "_evaluate_ab_test", mock_evaluate_ab_test)

    # Testar treinamento (com subconjunto pequeno para ser rápido)
    session = await pipeline.train_updated_model(data[:100], model_version="v_test")

    assert session.model_architecture == "GradientBoosting_ensemble"
    assert session.metrics_after["f1_score"] >= 0
    assert "f1_score" in session.improvement

    # Testar deploy logic
    # Forçar improvement para ser alto o suficiente para deploy
    session.improvement["f1_score"] = 0.05
    session.improvement["precision"] = 0.01
    session.metrics_after["auc_roc"] = 0.95

    deploy_res = await pipeline.deploy_with_canary(session, "v_test")
    assert deploy_res["status"] == "canary_deployed"

    # Verifica estatísticas
    stats = pipeline.get_retraining_statistics()
    assert stats["total_sessions"] == 1
