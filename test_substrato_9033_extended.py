import pytest
import asyncio
from arkhe_tv.deepfake_detector import DeepfakeDetector, DeepfakeSeverity
from arkhe_tv.ldm_controller import LDMController, LDMConfig, LDMMode

@pytest.mark.asyncio
async def test_deepfake_detector():
    detector = DeepfakeDetector()
    frames = [f"frame_{i:04d}_data".encode() for i in range(10)]
    report = await detector.analyze_stream("test_stream", frames)

    assert report.content_id == "test_stream"
    assert report.total_frames == 10
    assert isinstance(report.verdict, DeepfakeSeverity)

@pytest.mark.asyncio
async def test_ldm_controller():
    class MockXOS:
        async def get_active_plps(self):
            return [
                type('PLP', (), {'plp_id': 1, 'cnr_threshold_db': 28, 'bitrate_mbps': 8.0, 'phi_c': 0.97}),
                type('PLP', (), {'plp_id': 2, 'cnr_threshold_db': 22, 'bitrate_mbps': 18.0, 'phi_c': 0.94}),
            ]
        async def set_ldm_config(self, core_plp, enhanced_plp, injection_db):
            pass

    ldm = LDMController(
        xos_adapter=MockXOS(),
        config=LDMConfig(core_plp_id=1, enhanced_plp_id=2, injection_level_db=-10.0, mode=LDMMode.ADAPTIVE),
    )

    metrics = await ldm.get_current_metrics()
    assert metrics.core_layer_cnr_db == 33
    assert metrics.enhanced_layer_cnr_db == 25
    assert abs(metrics.phi_c_coherence - 0.958) < 0.01

    new_inj = await ldm.optimize()
    assert new_inj <= ldm.config.max_injection_db
    assert new_inj >= ldm.config.min_injection_db
