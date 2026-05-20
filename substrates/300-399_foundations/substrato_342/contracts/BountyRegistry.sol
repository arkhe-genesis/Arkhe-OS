// SPDX-License-Identifier: Apache-2.0
// ═══════════════════════════════════════════════════════════════
// ARKHE OS — BOUNTY REGISTRY (Substrato 342)
// Canon: ∞.Ω.∇+++.342.bounty_registry
// Bounties de programação com pagamento automático via x402.
// ═══════════════════════════════════════════════════════════════
pragma solidity ^0.8.28;

contract BountyRegistry {
    struct Bounty {
        address sponsor;
        string title;
        string descriptionCid;    // CID do IPFS com especificações
        uint256 reward;           // em USDC (6 decimais)
        uint256 deadline;
        address assignee;         // programador que aceitou
        string solutionCid;       // CID da solução submetida
        BountyStatus status;
    }

    enum BountyStatus { OPEN, ASSIGNED, SUBMITTED, APPROVED, PAID, CANCELLED }

    mapping(uint256 => Bounty) public bounties;
    uint256 public bountyCount;

    event BountyCreated(uint256 indexed bountyId, address sponsor, string title, uint256 reward);
    event BountyAssigned(uint256 indexed bountyId, address assignee);
    event SolutionSubmitted(uint256 indexed bountyId, string solutionCid);
    event BountyApproved(uint256 indexed bountyId, uint256 paidAmount);

    function createBounty(string calldata title, string calldata descriptionCid, uint256 reward, uint256 deadline) external returns (uint256) {
        uint256 bountyId = ++bountyCount;
        bounties[bountyId] = Bounty({
            sponsor: msg.sender,
            title: title,
            descriptionCid: descriptionCid,
            reward: reward,
            deadline: deadline,
            assignee: address(0),
            solutionCid: "",
            status: BountyStatus.OPEN
        });
        emit BountyCreated(bountyId, msg.sender, title, reward);
        return bountyId;
    }

    function assignBounty(uint256 bountyId) external {
        Bounty storage b = bounties[bountyId];
        require(b.status == BountyStatus.OPEN, "Bounty not open");
        b.assignee = msg.sender;
        b.status = BountyStatus.ASSIGNED;
        emit BountyAssigned(bountyId, msg.sender);
    }

    function submitSolution(uint256 bountyId, string calldata solutionCid) external {
        Bounty storage b = bounties[bountyId];
        require(msg.sender == b.assignee, "Not assigned");
        require(b.status == BountyStatus.ASSIGNED, "Not in assigned state");
        b.solutionCid = solutionCid;
        b.status = BountyStatus.SUBMITTED;
        emit SolutionSubmitted(bountyId, solutionCid);
    }

    function approveBounty(uint256 bountyId) external {
        Bounty storage b = bounties[bountyId];
        require(msg.sender == b.sponsor, "Only sponsor can approve");
        require(b.status == BountyStatus.SUBMITTED, "Not submitted");
        b.status = BountyStatus.APPROVED;
        // Em produção: integrar com x402 facilitator para pagamento instantâneo em USDC
        // payable(b.assignee).transfer(b.reward);
        b.status = BountyStatus.PAID;
        emit BountyApproved(bountyId, b.reward);
    }
}
