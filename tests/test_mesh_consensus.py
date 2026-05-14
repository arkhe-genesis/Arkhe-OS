import pytest
import asyncio
from arkhe.mesh.multi_llm_orchestrator import MultiLLMMeshGateway, LLMNodeConfig, LLMProvider
from arkhe.mesh.phi_c_consensus import PhiCConsensusEngine, ConsensusStrategy
from arkhe.layers.constraints import TemporalChainClient
from arkhe.kernel.ping_governance_v2 import PingGovernanceKernelV2
from arkhe.layers.auth_orcid import OrcidAuthProvider

@pytest.mark.asyncio
async def test_mesh_consensus():
    temporal = TemporalChainClient()
    governance = PingGovernanceKernelV2()
    auth = OrcidAuthProvider()
    gateway = MultiLLMMeshGateway(temporal, governance, auth)

    config = LLMNodeConfig(
        provider=LLMProvider.KIMI,
        node_id="kimi-test-1",
        api_endpoint="test",
        orcid="0000-0000-0000-0000"
    )
    gateway.register_node(config)
    await gateway.health_check("kimi-test-1")

    consensus = PhiCConsensusEngine(gateway, governance, temporal, min_respondents=1)
    result = await consensus.query_consensus("test query")

    assert result.winner_node_id == "kimi-test-1"
    assert "KIMI" in result.winner_response
