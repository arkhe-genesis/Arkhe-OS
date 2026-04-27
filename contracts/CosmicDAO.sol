// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./CosmicPoccVerifier.sol";

/**
 * @title CosmicDAO
 * @dev Scientific DAO for governance of the cosmological ΛCDM model.
 */
contract CosmicDAO {
    CosmicPoccVerifier public verifier;

    struct CosmologicalProposal {
        uint256 proposalId;
        address proposer;
        string parameterName;
        uint256 proposedValue;
        string justification;
        uint256 votingStartTime;
        uint256 votingEndTime;
        bool executed;
        uint256 zkVerifiedFor;
        uint256 zkVerifiedAgainst;
        bytes32 observationalDataCommitment;
    }

    mapping(uint256 => CosmologicalProposal) public proposals;
    uint256 public nextProposalId = 1;

    uint256 public currentPMinThreshold = 100;
    int256 public currentWDE = -1000;
    uint256 public currentH0Prior = 6740;

    event ProposalCreated(uint256 indexed proposalId, address proposer, string parameterName, uint256 proposedValue);
    event ZKVoteCast(uint256 indexed proposalId, address indexed voter, bool support);
    event ParameterUpdated(string parameterName, uint256 oldValue, uint256 newValue);

    constructor(address _verifier) {
        verifier = CosmicPoccVerifier(_verifier);
    }

    function proposeAdjustment(
        string calldata parameterName,
        uint256 proposedValue,
        string calldata justification
    ) external returns (uint256) {
        uint256 proposalId = nextProposalId++;
        proposals[proposalId] = CosmologicalProposal({
            proposalId: proposalId,
            proposer: msg.sender,
            parameterName: parameterName,
            proposedValue: proposedValue,
            justification: justification,
            votingStartTime: block.timestamp,
            votingEndTime: block.timestamp + 1 weeks,
            executed: false,
            zkVerifiedFor: 0,
            zkVerifiedAgainst: 0,
            observationalDataCommitment: bytes32(0)
        });

        emit ProposalCreated(proposalId, msg.sender, parameterName, proposedValue);
        return proposalId;
    }

    function castZKVote(
        uint256 proposalId,
        bool support,
        uint[2] calldata a, uint[2][2] calldata b, uint[2] calldata c,
        uint[2] calldata input
    ) external {
        require(verifier.verifyProof(a, b, c, input), "Invalid ZK vote");
        CosmologicalProposal storage proposal = proposals[proposalId];
        require(block.timestamp <= proposal.votingEndTime, "Voting ended");

        if (support) proposal.zkVerifiedFor++;
        else proposal.zkVerifiedAgainst++;

        emit ZKVoteCast(proposalId, msg.sender, support);
    }

    function executeProposal(uint256 proposalId) external {
        CosmologicalProposal storage proposal = proposals[proposalId];
        require(block.timestamp > proposal.votingEndTime, "Voting not ended");
        require(!proposal.executed, "Already executed");

        uint256 totalVotes = proposal.zkVerifiedFor + proposal.zkVerifiedAgainst;
        require(totalVotes >= 5, "Insufficient redundancy");
        require((proposal.zkVerifiedFor * 100) / totalVotes >= 66, "Consensus not reached");

        proposal.executed = true;
        _updateParameter(proposal.parameterName, proposal.proposedValue);
    }

    function _updateParameter(string memory parameterName, uint256 newValue) internal {
        bytes32 nameHash = keccak256(bytes(parameterName));
        uint256 oldValue;

        if (nameHash == keccak256(bytes("P_min"))) {
            oldValue = currentPMinThreshold;
            currentPMinThreshold = newValue;
        } else if (nameHash == keccak256(bytes("w_DE"))) {
            oldValue = uint256(int256(currentWDE));
            currentWDE = int256(newValue);
        } else if (nameHash == keccak256(bytes("H_0_prior"))) {
            oldValue = currentH0Prior;
            currentH0Prior = newValue;
        } else {
            revert("Unknown parameter");
        }

        emit ParameterUpdated(parameterName, oldValue, newValue);
    }
}
