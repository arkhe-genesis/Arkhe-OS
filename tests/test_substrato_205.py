import pytest
import asyncio
from sovereign_twin.token_arkhe_extended import SovereignTwinRegistry
from brics_plus.brics_plus_federation import BRICSPlusFederation
from security.architect_omega_protection import ArchitectOmegaProtection
from substrato_205_capsule_registration import TemporalChainMock, PhiBusMock, HSMMock

@pytest.mark.asyncio
async def test_create_sovereign_twin():
    registry = SovereignTwinRegistry(
        temporal_chain=TemporalChainMock(),
        phi_bus=PhiBusMock(),
        hsm_signer=HSMMock(),
        brics_federation=BRICSPlusFederation(),
        architect_protection=ArchitectOmegaProtection()
    )
    twin = await registry.create_sovereign_twin(
        creator_did="did:ethr:0xABCD1234",
        creator_orcid="0000-0000-0000-0000",
        workflow_digest="sha256:1234",
        ipfs_cid="ipfs://1234",
        evidence={},
        dao_seals=[],
        royalty_policy={},
        controller_wallets=[],
        attestations=[]
    )
    assert twin.twin_id is not None
    assert twin.data["creator_did"] == "did:ethr:0xABCD1234"
    assert twin.data["creator_orcid"] == "0000-0000-0000-0000"
