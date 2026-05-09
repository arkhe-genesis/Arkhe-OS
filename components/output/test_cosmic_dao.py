import pytest
from output.cosmic_dao_substrate_122 import CosmicDAO, ProposalType

@pytest.fixture
def test_dao():
    return CosmicDAO(federation_config={})

def test_initial_treasury(test_dao):
    assert test_dao.treasury_balance == 1000000.0

@pytest.mark.asyncio
async def test_submit_proposal(test_dao):
    test_dao.mint_governance_token("user1", 1000.0)
    test_dao.stake("user1", 200.0)

    proposal = await test_dao.submit_proposal(
        proposer="user1",
        proposal_type=ProposalType.TREASURY_ALLOCATION,
        title="Test Proposal",
        description="Allocate funds",
        merces_allocation=500.0,
        stake_amount=100.0
    )

    assert proposal is not None
    assert proposal.proposer == "user1"
    assert proposal.title == "Test Proposal"
