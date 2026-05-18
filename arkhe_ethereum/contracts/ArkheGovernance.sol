// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

interface IArkheIdentity {
    function identities(address agent) external view returns (string memory, bytes memory, uint256 reputation, bool isActive);
}

/**
 * @title ArkheGovernance
 * @dev Phi_C-Weighted DAO governance
 */
contract ArkheGovernance {
    IArkheIdentity public identityContract;

    struct Proposal {
        uint256 id;
        string description;
        uint256 forVotes;
        uint256 againstVotes;
        uint256 endTime;
        bool executed;
    }

    uint256 public proposalCounter;
    mapping(uint256 => Proposal) public proposals;
    mapping(uint256 => mapping(address => bool)) public hasVoted;

    event ProposalCreated(uint256 indexed id, string description, uint256 endTime);
    event Voted(uint256 indexed proposalId, address indexed voter, bool support, uint256 weight);
    event ProposalExecuted(uint256 indexed id);

    constructor(address _identityContract) {
        identityContract = IArkheIdentity(_identityContract);
    }

    function createProposal(string calldata description, uint256 votingDuration) external {
        (, , uint256 rep, bool isActive) = identityContract.identities(msg.sender);
        require(isActive, "Must be an active identity to propose");
        require(rep >= 100, "Insufficient reputation to propose");

        proposalCounter++;
        proposals[proposalCounter] = Proposal({
            id: proposalCounter,
            description: description,
            forVotes: 0,
            againstVotes: 0,
            endTime: block.timestamp + votingDuration,
            executed: false
        });

        emit ProposalCreated(proposalCounter, description, block.timestamp + votingDuration);
    }

    function vote(uint256 proposalId, bool support) external {
        Proposal storage proposal = proposals[proposalId];
        require(block.timestamp < proposal.endTime, "Voting period ended");
        require(!hasVoted[proposalId][msg.sender], "Already voted");

        (, , uint256 rep, bool isActive) = identityContract.identities(msg.sender);
        require(isActive, "Must be an active identity to vote");

        // The voting weight is proportional to the agent's reputation
        uint256 weight = rep > 0 ? rep : 1;

        if (support) {
            proposal.forVotes += weight;
        } else {
            proposal.againstVotes += weight;
        }

        hasVoted[proposalId][msg.sender] = true;
        emit Voted(proposalId, msg.sender, support, weight);
    }

    function executeProposal(uint256 proposalId) external {
        Proposal storage proposal = proposals[proposalId];
        require(block.timestamp >= proposal.endTime, "Voting period not ended");
        require(!proposal.executed, "Already executed");

        require(proposal.forVotes > proposal.againstVotes, "Proposal did not pass");

        proposal.executed = true;
        // In a real system, there would be executable code here

        emit ProposalExecuted(proposalId);
    }
}
