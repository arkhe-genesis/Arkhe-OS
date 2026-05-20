// SPDX-License-Identifier: Apache-2.0
// ═══════════════════════════════════════════════════════════════
// ARKHE OS — COMMUNITY DAO (Governança por Φ_C)
// Canon: ∞.Ω.∇+++.336.community_dao
// Membros votam com peso proporcional ao Φ_C.
// ═══════════════════════════════════════════════════════════════
pragma solidity ^0.8.28;

import "./ArkheIdentityNFT.sol";

contract CommunityDAO {
    struct Proposal {
        string description;
        uint256 votesFor;
        uint256 votesAgainst;
        uint256 deadline;
        bool executed;
    }

    mapping(uint256 => Proposal) public proposals;
    mapping(uint256 => mapping(uint256 => bool)) public hasVoted; // proposalId -> tokenId -> bool
    uint256 public proposalCount;
    ArkheIdentityNFT public identityContract;

    constructor(address _identityContract) {
        identityContract = ArkheIdentityNFT(_identityContract);
    }

    function createProposal(string calldata description, uint256 votingPeriod) external returns (uint256) {
        uint256 proposalId = ++proposalCount;
        proposals[proposalId] = Proposal(description, 0, 0, block.timestamp + votingPeriod, false);
        return proposalId;
    }

    function vote(uint256 proposalId, bool support) external {
        Proposal storage p = proposals[proposalId];
        require(block.timestamp < p.deadline, "Voting closed");

        uint256 tokenId = identityContract.tokenOfOwnerByIndex(msg.sender, 0);
        require(!hasVoted[proposalId][tokenId], "Already voted");
        hasVoted[proposalId][tokenId] = true;

        uint256 weight = identityContract.tokenToPhiC(tokenId); // Φ_C × 10⁹
        if (support) p.votesFor += weight;
        else p.votesAgainst += weight;
    }
}
