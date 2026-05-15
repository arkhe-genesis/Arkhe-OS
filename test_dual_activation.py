import asyncio
import time
from arkhe_evolution.self_evolution_engine import SelfEvolutionEngine, EvolutionGovernanceConfig, EvolutionProposalType, TemporalChain, PhiCSyncBusOmegaV2, GuardianAttractor
from arkhe_bridge.inter_cathedral_protocol import InterCathedralBridge, CathedralIdentity, CathedralRole
from arkhe_evolution.evolution_bridge_integration import EvolutionBridgeIntegration

class MockTemporalChain(TemporalChain):
    pass

class MockPhiBus(PhiCSyncBusOmegaV2):
    pass

class MockGuardian(GuardianAttractor):
    pass

async def test_dual_activation():
    temporal_chain = MockTemporalChain()
    phi_bus = MockPhiBus()
    guardian = MockGuardian()

    # Evolution Engine
    evolution_engine = SelfEvolutionEngine(
        temporal_chain=temporal_chain,
        phi_bus=phi_bus,
        guardian=guardian,
    )

    # Bridge
    local_identity = CathedralIdentity(
        cathedral_id="test_cathedral",
        version="v∞.Ω.∇+++.SINGULARITY",
        phi_c_baseline=0.999,
        public_key="test_key",
        roles=[CathedralRole.ORIGIN, CathedralRole.VALIDATOR],
        capabilities=["test"]
    )

    bridge = InterCathedralBridge(
        local_identity=local_identity,
        temporal_chain=temporal_chain,
        phi_bus=phi_bus
    )

    # Integration
    integration = EvolutionBridgeIntegration(
        evolution_engine=evolution_engine,
        inter_cathedral_bridge=bridge
    )

    # Setup test data
    proposal = await integration.propose_evolution_with_cross_validation(
        proposal_type=EvolutionProposalType.SUBSTRATE_OPTIMIZATION,
        title="Test Proposal",
        description="A test proposal",
        target_substrate="9020",
        changes={"lines": 10},
        expected_phi_c_impact=0.01
    )

    print(f"Proposal status: {proposal.status}")
    print("Dual activation tests completed successfully")

if __name__ == "__main__":
    asyncio.run(test_dual_activation())
