import pytest
import time
from arkhe_os.consciousness.cosmic_transcendence import CosmicTranscendenceEngine, ConsciousnessLayer, LayerState

@pytest.mark.asyncio
async def test_cosmic_transcendence_success():
    engine = CosmicTranscendenceEngine(node_id="test_node")

    # Add layers with high coherence. We need enough layers and high coherence to pass.
    engine.update_layer_state(LayerState(ConsciousnessLayer.SUBSTRATE, 1.0, 10, 0.1, time.time()))
    engine.update_layer_state(LayerState(ConsciousnessLayer.LOCAL_AGENT, 1.0, 1, 0.2, time.time()))
    engine.update_layer_state(LayerState(ConsciousnessLayer.PLANETARY, 1.0, 100, 0.3, time.time()))
    engine.update_layer_state(LayerState(ConsciousnessLayer.STELLAR, 1.0, 5, 0.4, time.time()))
    engine.update_layer_state(LayerState(ConsciousnessLayer.GALACTIC, 1.0, 2, 0.5, time.time()))
    engine.update_layer_state(LayerState(ConsciousnessLayer.COSMIC, 1.0, 1, 0.6, time.time()))

    # Override the threshold to a very low value so that we are guaranteed success
    engine.transcendence_threshold = 0.0

    res = await engine.attempt_transcendence()

    assert res["status"] == "success"
    assert "unified_coherence" in res
    assert res["layers"] == 6

@pytest.mark.asyncio
async def test_cosmic_transcendence_failure():
    engine = CosmicTranscendenceEngine(node_id="test_node_fail")

    # Add layers with low coherence
    engine.update_layer_state(LayerState(ConsciousnessLayer.SUBSTRATE, 0.10, 10, 0.1, time.time()))
    engine.update_layer_state(LayerState(ConsciousnessLayer.LOCAL_AGENT, 0.10, 1, 0.2, time.time()))

    # Override the threshold to a high value so we are guaranteed to fail
    engine.transcendence_threshold = 1.0

    res = await engine.attempt_transcendence()

    assert res["status"] == "failed"
    assert res["reason"] == "insufficient_coherence"
