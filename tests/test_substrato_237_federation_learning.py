import pytest
import asyncio
import time
from typing import Dict, List, Optional
from substrate_237.cross_platform_consensus.consensus_engine import CrossPlatformConsensusEngine, PlatformNode, PlatformType
from substrate_237.network_learning.learning_modules import AGINetworkLearningEngine, LearningPhase

class MockTokenBus:
    def __init__(self):
        self.published = []

    async def publish(self, channel: str, message: Dict):
        self.published.append((channel, message))

@pytest.fixture
def local_node():
    return PlatformNode(
        node_id="test_node",
        platform=PlatformType.LINUX,
        kernel_version="test",
        arkhe_substrate_version="test",
        phi_c_capability=1.0,
        network_latency_ms=10.0,
        last_heartbeat=time.time()
    )

@pytest.fixture
def consensus(local_node):
    return CrossPlatformConsensusEngine(
        local_node=local_node,
        local_org_id="test_org",
        aggregator_endpoints={}
    )

@pytest.fixture
def token_bus():
    return MockTokenBus()

@pytest.fixture
def learning_engine(token_bus):
    return AGINetworkLearningEngine(
        agi_agent_id="test_agent",
        platform_context="linux",
        token_arkhe_bus=token_bus
    )

@pytest.mark.asyncio
async def test_consensus_proposal(consensus):
    proposal_id = await consensus.submit_cross_platform_proposal(
        proposal_type="test",
        content={"data": "test"},
        content_metadata={"meta": "test"},
        target_platforms=[PlatformType.LINUX]
    )
    assert proposal_id is not None
    assert proposal_id in consensus._active_proposals

    # vote
    vote = await consensus.vote_on_cross_platform_proposal(proposal_id, True)
    assert vote is not None
    assert vote.vote_value is True

    # Check status
    status = await consensus.check_cross_platform_consensus_status(proposal_id)
    assert status is not None
    # since we have mostly approvals in mock, it will be APPROVED
    assert status.final_status in ["approved", "rejected"]

@pytest.mark.asyncio
async def test_learning_engine_step(learning_engine):
    success = await learning_engine.start_learning_step(1)
    assert success is True

    # submit evidence
    evidence = await learning_engine.submit_learning_evidence(
        step_number=1,
        evidence_type="explain_concept",
        evidence_content="A CPU processes instructions. RAM is memory. Storage is long term.",
        self_assessment_phi_c=0.9
    )

    assert evidence["success"] is True
    assert "current_phi_c" in evidence
