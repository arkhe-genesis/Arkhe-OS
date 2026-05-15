import pytest
import numpy as np
from arkhe_continental_mind.blueprint_178a import (
    MAC_Protocol_v2,
    PhiC_Bus_Distributed,
    InterLLMMessage
)
from arkhe_continental_mind.orchestrator_178b import ContinentalMindOrchestrator
from arkhe_continental_mind.feedback_loop import EvolutionaryFeedbackLoop
from arkhe_continental_mind.federated_privacy import DifferentialPrivacyValidator

class MockGuardian:
    async def exorcise(self, content):
        return True, None

class MockTemporalAnchor:
    async def anchor_event(self, event_type, payload):
        return "mock_seal_123"

@pytest.fixture
def orchestrator():
    consensus_engine = MAC_Protocol_v2()
    phi_bus = PhiC_Bus_Distributed()
    guardian = MockGuardian()
    temporal_anchor = MockTemporalAnchor()
    return ContinentalMindOrchestrator(consensus_engine, phi_bus, guardian, temporal_anchor)

@pytest.mark.asyncio
async def test_route_message(orchestrator):
    msg = InterLLMMessage(content="Hello", intent="test")
    response = await orchestrator.route_message(msg)

    assert response.rejected is False
    assert response.confidence == 0.9999
    assert response.content == "Consensus Reached"
    assert response.temporal_seal == "mock_seal_123"

@pytest.mark.asyncio
async def test_feedback_loop_execution(orchestrator):
    loop = EvolutionaryFeedbackLoop(orchestrator)

    # We override run_loop slightly to ensure it doesn't block infinitely
    # but the logic runs once.
    await loop.run_loop()

    # Check if adjustments were made
    assert len(orchestrator.consensus_engine.node_weights) == 0 # our mock data has everything perfectly at 0.99 so no penalization or rewards

@pytest.mark.asyncio
async def test_detect_decoherence_patterns():
    loop = EvolutionaryFeedbackLoop(None)
    metrics = {
        "node_good": [0.995, 0.996],
        "node_bad": [0.90, 0.92]
    }
    patterns = await loop._detect_decoherence_patterns(metrics)
    assert "node_good" in patterns["high_coherence_nodes"]
    assert "node_bad" in patterns["low_coherence_nodes"]

def test_differential_privacy():
    validator = DifferentialPrivacyValidator(epsilon=1.0)
    data = np.array([0.5, 0.5])
    noisy = validator.add_laplace_noise(data, sensitivity=1.0)

    # Ruído deve ter mudado o array original
    assert not np.array_equal(data, noisy)

    # Validação simples
    assert validator.validate_gradient_update(noisy, sensitivity=1.0) is True

    # Gradiente imenso deve ser rejeitado
    huge_grad = np.array([100.0, 100.0])
    assert validator.validate_gradient_update(huge_grad, sensitivity=1.0) is False
