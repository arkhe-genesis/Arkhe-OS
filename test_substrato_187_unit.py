import pytest
import asyncio
import numpy as np
import cv2
from PIL import Image
import os
from unittest.mock import patch, MagicMock

from risomorphism.engine.real_image_processor import RealImageProcessor, ImageProcessingConfig
from risomorphism.video.eikon_generator import RealEikonGenerator, EikonConfig
from transparency.ascii_report_automation import ASCIIReportAutomation, HSMConfig
from api.debug_braille_endpoint import app
from fastapi.testclient import TestClient
from broadcast.eikon_overlay_integration import EikonOverlayIntegrator, EikonOverlayConfig
from security.visual_pqc_signature import VisualPQCSignature
from federation.visual_federation_protocol import VisualFederationProtocol, FederationConfig, VisualAssetType

@pytest.fixture
def dummy_image(tmp_path):
    img = Image.fromarray(np.random.randint(0, 255, (100, 100), dtype=np.uint8))
    path = tmp_path / "dummy.png"
    img.save(path)
    return str(path)

@pytest.fixture
def dummy_video(tmp_path):
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    path = tmp_path / "dummy.mp4"
    out = cv2.VideoWriter(str(path), fourcc, 20.0, (100, 100))
    for _ in range(10):
        frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        out.write(frame)
    out.release()
    return str(path)

def test_real_image_processor(dummy_image):
    proc = RealImageProcessor()
    norm = proc.load_and_preprocess(dummy_image, (50, 50))
    assert norm.shape == (50, 50)
    ascii_out = proc.map_to_glyphs(norm, "stroke-clarity")
    assert len(ascii_out.split('\n')) == 50
    metrics = proc.calculate_quality_metrics(ascii_out, norm)
    assert 'verdict' in metrics

@pytest.mark.asyncio
async def test_eikon_generator(dummy_video, tmp_path):
    out_html = str(tmp_path / "dummy.html")
    gen = RealEikonGenerator(EikonConfig(dummy_video, out_html))
    res = await gen.generate_eikon()
    assert res['input_video'] == dummy_video
    assert os.path.exists(out_html)

@pytest.mark.asyncio
async def test_ascii_report_automation():
    auto = ASCIIReportAutomation("http://dummy", HSMConfig())
    res = await auto.generate_daily_cover()
    assert 'report_date' in res
    assert 'cover_hash' in res

def test_debug_braille_endpoint():
    client = TestClient(app)
    # Unauthorized
    response = client.post("/debug/braille", json={"agent_id": "test"})
    assert response.status_code == 401

    # Authorized but agent not found
    response = client.post("/debug/braille", headers={"Authorization": "Bearer arkhe-debug-token"}, json={"agent_id": "invalid"})
    assert response.status_code == 404

    # Authorized and valid agent
    response = client.post("/debug/braille", headers={"Authorization": "Bearer arkhe-debug-token"}, json={"agent_id": "agent-financial-risk-01"})
    assert response.status_code == 200
    assert response.json()["success"] == True
    assert "⠷⠁⠗⠅⠓⠑" in response.json()["braille_output"]

@pytest.mark.asyncio
async def test_eikon_overlay_integrator(tmp_path):
    out_html = str(tmp_path / "dummy.html")
    with open(out_html, "w") as f:
        f.write("dummy")
    class MockHlsInjector:
        async def inject_overlay(self, *args, **kwargs):
            pass
    class MockPhiBus:
        def get_mesh_coherence(self):
            return 0.999
        async def subscribe(self, topic, handler):
            pass

    over = EikonOverlayIntegrator(EikonOverlayConfig("stream1", out_html), hls_injector=MockHlsInjector(), phi_bus=MockPhiBus())
    await over._on_critical_alert({"type": "test"})
    assert over._overlay_active == True

@pytest.mark.asyncio
async def test_visual_pqc_signature():
    sig = VisualPQCSignature()
    res = await sig.generate_visual_signature("deadbeef", {"algorithm": "Dilithium-3", "key_id": "test"})
    assert 'visual_signature' in res
    assert sig.verify_visual_signature(res['visual_signature'], res['integrity_hash']) == True

@pytest.mark.asyncio
async def test_visual_federation_protocol():
    fed = VisualFederationProtocol(FederationConfig("org1", {"org1", "org2"}))
    res = await fed.publish_asset(VisualAssetType.ASCII_RENDER, "content", {"meta": "data"})
    assert res.source_org_id == "org1"

    fetched = await fed.fetch_asset(res.asset_id, "org2")
    assert fetched['asset_id'] == res.asset_id
