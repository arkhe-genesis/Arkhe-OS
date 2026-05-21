// SPDX-License-Identifier: MIT OR Apache-2.0
pragma solidity ^0.8.24;

import "./InvariantGuard.sol";

interface IDisputeControl {
    function isIsolated(address node) external view returns (bool);
}

// ═══════════════════════════════════════════════════════════════════
// ConsensusPool.sol — Consenso distribuído com staking
// ═══════════════════════════════════════════════════════════════════

contract ConsensusPool is InvariantGuard {
    struct Validator {
        address addr;
        uint256 stake;
        uint256 phiC;
        uint8 tier;
        bool active;
        uint256 lastVote;
    }

    mapping(address => Validator) public validators;
    uint256 public totalStake;
    uint256 public constant QUORUM = 76; // 76% = 3/4 majority
    IDisputeControl public disputeControl;

    event BlockProposed(
        uint256 indexed blockNumber,
        address indexed proposer,
        bytes32 merkleRoot,
        uint256 phiC,
        uint256 votes
    );

    // Propor novo bloco com validação de invariante
    function proposeBlock(
        bytes32 previousHash,
        bytes32 merkleRoot,
        uint256 phiC
    )
        external
        aboveGhost(phiC)
        belowGap(phiC)
        returns (bool)
    {
        Validator storage proposer = validators[msg.sender];
        require(proposer.active, "Validator not active");

        // Registrar proposta
        emit BlockProposed(
            block.number,
            msg.sender,
            merkleRoot,
            phiC,
            0 // votes to be collected
        );

        return true;
    }

    // Submeter prova de inferência com controle de disputas
    function submitInferenceProof(
        bytes32 proofHash,
        bytes calldata data
    ) external {
        if (address(disputeControl) != address(0) && disputeControl.isIsolated(msg.sender)) {
            revert("Node is isolated due to disputes");
        }
    }

    // Votar em bloco proposto
    function voteOnBlock(
        uint256 blockNumber,
        bool approve
    ) external returns (bool) {
        Validator storage voter = validators[msg.sender];
        require(voter.active, "Validator not active");

        // Lógica de consenso cross-tier simplificada
        // (implementação completa em produção)

        return true;
    }
}
