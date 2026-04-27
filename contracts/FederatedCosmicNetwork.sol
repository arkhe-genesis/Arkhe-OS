// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IFederatedConsensusVerifier {
    function verifyProof(
        uint[2] calldata a,
        uint[2][2] calldata b,
        uint[2] calldata c,
        uint[3] calldata input
    ) external view returns (bool);
}

contract FederatedCosmicNetwork {
    IFederatedConsensusVerifier public consensusVerifier;

    enum ObservationMethod { CMB, BAO, SUPERNOVAE, LENSING, OTHER }

    struct SurveyNode {
        string name;
        ObservationMethod method;
        bytes32 publicKeyCommitment;
        bool isActive;
    }

    struct ConsensusRound {
        uint256 roundId;
        uint256 z_start;
        uint256 z_end;
        uint256 delta_p_max_allowed;
        uint256 requiredMethodologies;
        uint256 methodCount;
        bool consensusReached;
        bytes32 finalCommitment;
    }

    struct Proof {
        bytes32 surveyId;
        uint256 redshift;
        uint256 pOccCommitment;
        uint256 phiQCommitment;
        uint256 timestamp;
        bool verified;
    }

    mapping(address => SurveyNode) public surveyNodes;
    mapping(uint256 => ConsensusRound) public rounds;
    mapping(uint256 => mapping(ObservationMethod => bool)) public methodUsedInRound;
    mapping(bytes32 => Proof) public proofs;
    uint256 public currentRoundId;

    event SurveyRegistered(string name, ObservationMethod method);
    event ConsensusProofSubmitted(uint256 roundId, address survey, ObservationMethod method);
    event ParadigmShiftFederated(uint256 roundId, string newModel, bytes32 consensusCommitment);
    event SurveyProofSubmitted(bytes32 indexed surveyId, uint256 redshift, uint256 timestamp);

    constructor(address _verifier) {
        consensusVerifier = IFederatedConsensusVerifier(_verifier);
    }

    function registerSurvey(
        string calldata name,
        ObservationMethod method,
        bytes32 pubKeyCommitment
    ) external {
        require(!surveyNodes[msg.sender].isActive, "Already registered");
        surveyNodes[msg.sender] = SurveyNode(name, method, pubKeyCommitment, true);
        emit SurveyRegistered(name, method);
    }

    /**
     * @dev Submete uma prova individual de survey.
     */
    function submitSurveyProof(
        uint[2] calldata a,
        uint[2][2] calldata b,
        uint[2] calldata c,
        uint[2] calldata input,
        bytes32 surveyId,
        uint256 redshift,
        uint256 pOccCommitment,
        uint256 phiQCommitment
    ) external {
        // Em produção, verificar a prova ZK individual aqui.
        // require(individualVerifier.verifyProof(a, b, c, input), "Invalid Proof");

        proofs[surveyId] = Proof({
            surveyId: surveyId,
            redshift: redshift,
            pOccCommitment: pOccCommitment,
            phiQCommitment: phiQCommitment,
            timestamp: block.timestamp,
            verified: true
        });

        emit SurveyProofSubmitted(surveyId, redshift, block.timestamp);
    }

    function startConsensusRound(
        uint256 z_start,
        uint256 z_end,
        uint256 delta_p_max
    ) external {
        currentRoundId++;
        ConsensusRound storage r = rounds[currentRoundId];
        r.roundId = currentRoundId;
        r.z_start = z_start;
        r.z_end = z_end;
        r.delta_p_max_allowed = delta_p_max;
        r.requiredMethodologies = 3;
    }

    function submitFederatedProof(
        uint256 roundId,
        uint[2] calldata proof_a,
        uint[2][2] calldata proof_b,
        uint[2] calldata proof_c,
        uint[3] calldata publicSignals
    ) external {
        require(surveyNodes[msg.sender].isActive, "Not authorized");
        ConsensusRound storage r = rounds[roundId];
        require(!r.consensusReached, "Round closed");

        require(consensusVerifier.verifyProof(proof_a, proof_b, proof_c, publicSignals), "Invalid ZK proof");
        require(publicSignals[0] == r.delta_p_max_allowed, "Wrong tolerance");

        ObservationMethod method = surveyNodes[msg.sender].method;
        require(!methodUsedInRound[roundId][method], "Methodology already represented");

        r.methodCount++;
        methodUsedInRound[roundId][method] = true;

        emit ConsensusProofSubmitted(roundId, msg.sender, method);

        if (r.methodCount >= r.requiredMethodologies) {
            r.consensusReached = true;
            r.finalCommitment = bytes32(publicSignals[2]);
            emit ParadigmShiftFederated(roundId, "Xi-CDM Federated", r.finalCommitment);
        }
    }

    function getNetworkStatus() external view returns (
        uint256 totalSurveys,
        uint256 activeRound,
        bool consensusAchieved
    ) {
        return (0, currentRoundId, rounds[currentRoundId].consensusReached);
    }
}
