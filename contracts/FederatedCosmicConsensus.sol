// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "@openzeppelin/contracts/utils/cryptography/MessageHashUtils.sol";

// Interface para o verificador gerado pelo snarkjs
interface ICosmicPoccVerifier {
    function verifyProof(
        uint[2] calldata a,
        uint[2][2] calldata b,
        uint[2] calldata c,
        uint[2] calldata input
    ) external view returns (bool);
}

/**
 * @dev Contrato para consenso geométrico distribuído entre surveys cosmológicos
 */
contract FederatedCosmicConsensus {
    using ECDSA for bytes32;

    ICosmicPoccVerifier public individualProofVerifier;

    struct FederatedConsensusRound {
        bytes32 roundId;
        string parameterName;
        address[] participatingValidators;
        uint256 expectedNumProofs;
        uint256 numValidProofs;
        uint256 totalConsensusWeight;
        uint256 weightedSum;
        bool tensionDetected;
        bytes32 finalValueCommitment;
        uint256 startTime;
        uint256 endTime;
        bool finalized;
        string resolutionMethod;
    }

    mapping(bytes32 => FederatedConsensusRound) public consensusRounds;

    uint256 public constant MIN_CONSENSUS_RATIO = 70;
    uint256 public constant CONSENSUS_TIMEOUT = 7 days;

    event ConsensusRoundStarted(
        bytes32 indexed roundId,
        string parameterName,
        uint256 expectedNumSurveys,
        uint256 startTime
    );

    event ProofAggregated(
        bytes32 indexed roundId,
        bytes32 proofCommitment,
        uint256 numValidProofs,
        uint256 consensusWeight
    );

    event ConsensusFinalized(
        bytes32 indexed roundId,
        bytes32 finalValueCommitment,
        uint256 geometricConvergenceScore,
        uint256 timestamp
    );

    constructor(address _individualProofVerifier) {
        individualProofVerifier = ICosmicPoccVerifier(_individualProofVerifier);
    }

    function startConsensusRound(
        string calldata parameterName,
        uint256 expectedNumProofs,
        address[] calldata validators
    ) external returns (bytes32) {
        require(bytes(parameterName).length > 0, "Invalid parameter name");
        require(expectedNumProofs >= 3, "Minimum 3 surveys required");
        require(validators.length >= 3, "Minimum 3 validators required");

        bytes32 roundId = keccak256(abi.encodePacked(
            parameterName,
            block.timestamp,
            msg.sender,
            expectedNumProofs
        ));

        FederatedConsensusRound storage round = consensusRounds[roundId];
        round.roundId = roundId;
        round.parameterName = parameterName;
        round.participatingValidators = validators;
        round.expectedNumProofs = expectedNumProofs;
        round.startTime = block.timestamp;

        emit ConsensusRoundStarted(roundId, parameterName, expectedNumProofs, block.timestamp);
        return roundId;
    }

    function submitAggregatedProof(
        bytes32 roundId,
        uint[2] calldata a,
        uint[2][2] calldata b,
        uint[2] calldata c,
        uint[2] calldata input,
        uint256 consensusWeightTotal,
        uint256 weightedSumTotal,
        bool tensionFlag,
        bytes32 finalCommitment,
        bytes calldata signature
    ) external {
        FederatedConsensusRound storage round = consensusRounds[roundId];
        require(!round.finalized, "Round already finalized");
        require(_isAuthorizedValidator(round, msg.sender), "Not authorized validator");

        require(individualProofVerifier.verifyProof(a, b, c, input), "Invalid ZK proof");

        bytes32 messageHash = MessageHashUtils.toEthSignedMessageHash(keccak256(abi.encodePacked(
            roundId,
            input[0],
            input[1],
            consensusWeightTotal,
            weightedSumTotal,
            tensionFlag,
            finalCommitment
        )));
        address signer = messageHash.recover(signature);
        require(_isAuthorizedAggregator(signer), "Invalid aggregator signature");

        round.numValidProofs = input[0];
        round.totalConsensusWeight = consensusWeightTotal;
        round.weightedSum = weightedSumTotal;
        round.tensionDetected = tensionFlag;
        round.finalValueCommitment = finalCommitment;

        emit ProofAggregated(roundId, finalCommitment, round.numValidProofs, consensusWeightTotal);
    }

    function finalizeConsensus(
        bytes32 roundId,
        uint256 geometricConvergenceScore
    ) external {
        FederatedConsensusRound storage round = consensusRounds[roundId];
        require(!round.finalized, "Round finalized");
        require(round.finalValueCommitment != bytes32(0), "No proof");

        uint256 consensusRatio = (round.numValidProofs * 100) / round.expectedNumProofs;
        require(consensusRatio >= MIN_CONSENSUS_RATIO, "Insufficient ratio");

        round.endTime = block.timestamp;
        round.finalized = true;

        emit ConsensusFinalized(roundId, round.finalValueCommitment, geometricConvergenceScore, block.timestamp);
    }

    function _isAuthorizedValidator(FederatedConsensusRound storage round, address validator) internal view returns (bool) {
        for (uint256 i = 0; i < round.participatingValidators.length; i++) {
            if (round.participatingValidators[i] == validator) return true;
        }
        return false;
    }

    function _isAuthorizedAggregator(address aggregator) internal pure returns (bool) {
        return true;
    }
}
