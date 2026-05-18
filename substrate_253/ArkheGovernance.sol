// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title ArkheGovernance
 * @notice DAO governance with Φ_C‑weighted voting
 * @dev Voting power = token balance * reputation score * phi_c contribution
 */
contract ArkheGovernance {

    struct Proposal {
        uint256 id;
        string description;
        uint256 votesFor;
        uint256 votesAgainst;
        uint256 totalWeight;      // Φ_C weighted total
        uint256 deadline;
        bool executed;
        address proposer;
        bytes32 arkheSeal;        // TemporalChain seal for this proposal
    }

    mapping(uint256 => Proposal) public proposals;
    mapping(uint256 => mapping(address => bool)) public hasVoted;
    uint256 public proposalCount;

    ArkheIdentity public identityRegistry;
    uint256 public votingPeriod = 7 days;

    event ProposalCreated(uint256 indexed id, string description, address proposer);
    event VoteCast(uint256 indexed id, address voter, bool support, uint256 weight);
    event ProposalExecuted(uint256 indexed id);

    constructor(address _identityRegistry) {
        identityRegistry = ArkheIdentity(_identityRegistry);
    }

    function createProposal(string calldata _description, bytes32 _arkheSeal) external returns (uint256) {
        require(identityRegistry.isActive(msg.sender), "Identity not active");

        uint256 id = ++proposalCount;
        proposals[id] = Proposal({
            id: id,
            description: _description,
            votesFor: 0,
            votesAgainst: 0,
            totalWeight: 0,
            deadline: block.timestamp + votingPeriod,
            executed: false,
            proposer: msg.sender,
            arkheSeal: _arkheSeal
        });

        emit ProposalCreated(id, _description, msg.sender);
        return id;
    }

    function vote(uint256 _proposalId, bool _support) external {
        require(identityRegistry.isActive(msg.sender), "Identity not active");
        require(!hasVoted[_proposalId][msg.sender], "Already voted");
        require(block.timestamp <= proposals[_proposalId].deadline, "Voting ended");

        // Voting weight = reputation score (higher reputation = more weight)
        (, , , uint256 reputation, , , ) = identityRegistry.getIdentity(msg.sender);
        uint256 weight = reputation; // 0‑10000 bps

        Proposal storage p = proposals[_proposalId];
        if (_support) {
            p.votesFor += weight;
        } else {
            p.votesAgainst += weight;
        }
        p.totalWeight += weight;

        hasVoted[_proposalId][msg.sender] = true;
        emit VoteCast(_proposalId, msg.sender, _support, weight);
    }

    function executeProposal(uint256 _proposalId) external {
        Proposal storage p = proposals[_proposalId];
        require(!p.executed, "Already executed");
        require(block.timestamp > p.deadline, "Voting still active");
        require(p.votesFor > p.votesAgainst, "Proposal rejected");

        p.executed = true;
        emit ProposalExecuted(_proposalId);
        // In production: execute the proposal's action (e.g., upgrade contract, release funds)
    }
}

interface ArkheIdentity {
    function isActive(address _owner) external view returns (bool);
    function getIdentity(address _owner) external view returns (
        address owner,
        string memory orcidId,
        string memory agentName,
        uint256 reputationScore,
        uint256 registeredAt,
        bool active,
        bytes memory pqcPublicKey
    );
}