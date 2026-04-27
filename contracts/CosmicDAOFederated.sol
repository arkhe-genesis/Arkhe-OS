// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./CosmicPoccVerifier.sol";

/**
 * @title CosmicDAOFederated
 * @dev Manages federated validation of cosmic parameters across multiple surveys.
 */
contract CosmicDAOFederated {
    CosmicPoccVerifier public verifier;

    struct SurveyProof {
        bytes32 surveyId;
        uint256 redshift;
        uint256 pOccCommitment;
        uint256 phiQCommitment;
        uint256 timestamp;
        bool verified;
    }

    struct FederatedConsensus {
        uint256 roundId;
        uint256 startTime;
        uint256 endTime;
        uint256 requiredSurveys;
        uint256 currentApprovals;
        uint256 currentRejections;
        mapping(bytes32 => bool) hasVoted;
        bool consensusReached;
        uint256 newPMinThreshold;
    }

    mapping(bytes32 => SurveyProof) public proofs;
    mapping(uint256 => FederatedConsensus) public consensusRounds;
    uint256 public consensusRoundCount;

    uint256 public currentPMinThreshold = 100; // 1e-122 scaled by 1e120
    uint256 public constant MIN_SURVEYS = 3;
    uint256 public constant CONSENSUS_THRESHOLD = 66;

    event SurveyProofSubmitted(bytes32 indexed surveyId, uint256 redshift, uint256 timestamp);
    event ConsensusRoundStarted(uint256 indexed roundId, uint256 requiredSurveys);
    event ConsensusReached(uint256 indexed roundId, uint256 newPMin);
    event ConsensusFailed(uint256 indexed roundId, string reason);

    constructor(address _verifier) {
        verifier = CosmicPoccVerifier(_verifier);
    }

    function submitSurveyProof(
        uint[2] calldata a, uint[2][2] calldata b, uint[2] calldata c,
        uint[2] calldata input,
        bytes32 surveyId,
        uint256 redshift,
        uint256 pOccCommitment,
        uint256 phiQCommitment
    ) external {
        require(verifier.verifyProof(a, b, c, input), "Invalid proof");
        require(proofs[surveyId].timestamp == 0, "Proof already submitted");

        proofs[surveyId] = SurveyProof({
            surveyId: surveyId,
            redshift: redshift,
            pOccCommitment: pOccCommitment,
            phiQCommitment: phiQCommitment,
            timestamp: block.timestamp,
            verified: true
        });

        emit SurveyProofSubmitted(surveyId, redshift, block.timestamp);
    }

    function startConsensusRound(uint256 duration) external {
        consensusRoundCount++;
        FederatedConsensus storage round = consensusRounds[consensusRoundCount];
        round.roundId = consensusRoundCount;
        round.startTime = block.timestamp;
        round.endTime = block.timestamp + duration;
        round.requiredSurveys = MIN_SURVEYS;

        emit ConsensusRoundStarted(consensusRoundCount, MIN_SURVEYS);
    }

    function voteOnConsensus(uint256 roundId, bytes32 surveyId, bool approve) external {
        FederatedConsensus storage round = consensusRounds[roundId];
        require(block.timestamp >= round.startTime && block.timestamp <= round.endTime, "Not active");
        require(proofs[surveyId].verified, "Survey proof required");
        require(!round.hasVoted[surveyId], "Already voted");

        round.hasVoted[surveyId] = true;
        if (approve) round.currentApprovals++;
        else round.currentRejections++;

        if (round.currentApprovals + round.currentRejections >= round.requiredSurveys) {
            _finalizeConsensus(roundId);
        }
    }

    function _finalizeConsensus(uint256 roundId) internal {
        FederatedConsensus storage round = consensusRounds[roundId];
        uint256 total = round.currentApprovals + round.currentRejections;
        if (total == 0) return;

        uint256 approvalRate = (round.currentApprovals * 100) / total;

        if (approvalRate >= CONSENSUS_THRESHOLD) {
            round.consensusReached = true;
            round.newPMinThreshold = currentPMinThreshold * 105 / 100;
            currentPMinThreshold = round.newPMinThreshold;
            emit ConsensusReached(roundId, round.newPMinThreshold);
        } else {
            emit ConsensusFailed(roundId, "Approval rate below threshold");
        }
    }

    function getConsensusStatus(uint256 roundId) external view returns (
        uint256 approvals, uint256 rejections, bool reached, uint256 newPMin
    ) {
        FederatedConsensus storage round = consensusRounds[roundId];
        return (round.currentApprovals, round.currentRejections, round.consensusReached, round.newPMinThreshold);
    }
}
