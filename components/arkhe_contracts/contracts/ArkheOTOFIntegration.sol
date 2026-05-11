// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "./interfaces/IVerifier.sol";

interface IArkheOTOFSubsidyManager {
    function setGeneticVerified(bytes32 geneticHash) external;
}

/**
 * @title ArkheOTOFIntegration
 * @notice Integração de verificação ZK + medição G_info on-chain
 * @dev Combina prova ZK de elegibilidade OTOF com validação G_info
 */
contract ArkheOTOFIntegration is AccessControl, ReentrancyGuard {

    // ====================
    // ROLES
    // ====================
    bytes32 public constant ORACLE_ROLE = keccak256("ORACLE_ROLE");
    bytes32 public constant AUDITOR_ROLE = keccak256("AUDITOR_ROLE");

    // ====================
    // STATE
    // ====================
    IVerifier public verifier;
    IArkheOTOFSubsidyManager public subsidyManager;

    // Mapeamento: nullifier → status (usado para prevenir double-claim)
    mapping(bytes32 => bool) public nullifierUsed;

    // Thresholds G_info (scaled by 100)
    uint256 public gInfoMinThreshold = 85;       // 0.85 * 100
    uint256 public coherenceMinThreshold = 90;    // 0.90 * 100
    uint256 public entropyMaxThreshold = 15;       // 0.15 * 100

    // Contador de elegíveis
    uint256 public totalEligible;

    // ====================
    // EVENTS
    // ====================
    event EligibilityVerified(
        address indexed patient,
        bytes32 nullifier,
        uint256 gInfo,
        uint256 coherence,
        bool approved
    );

    event GInfoThresholdUpdated(
        string metric,
        uint256 oldValue,
        uint256 newValue
    );

    // ====================
    // CONSTRUCTOR
    // ====================
    constructor(address _verifier, address _subsidyManager) {
        verifier = IVerifier(_verifier);
        subsidyManager = IArkheOTOFSubsidyManager(_subsidyManager);
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
    }

    // ====================
    // EXTERNAL FUNCTIONS
    // ====================

    /**
     * @notice Verifica elegibilidade com prova ZK + validação G_info
     */
    function verifyEligibility(
        uint256[2] memory a,
        uint256[2][2] memory b,
        uint256[2] memory c,
        uint256[3] memory publicInputs,
        uint256 gInfo,
        uint256 coherence,
        uint256 entropy
    ) external nonReentrant returns (bool approved) {

        bool validProof = verifier.verifyProof(a, b, c, publicInputs);
        require(validProof, "Invalid ZK proof");

        bytes32 nullifier = bytes32(publicInputs[1]);
        require(!nullifierUsed[nullifier], "Nullifier already used");
        nullifierUsed[nullifier] = true;

        bool gInfoValid = gInfo >= gInfoMinThreshold;
        bool coherenceValid = coherence >= coherenceMinThreshold;
        bool entropyValid = entropy <= entropyMaxThreshold;

        approved = gInfoValid && coherenceValid && entropyValid;

        if (approved) {
            totalEligible++;
            subsidyManager.setGeneticVerified(bytes32(publicInputs[2]));
        }

        emit EligibilityVerified(
            msg.sender,
            nullifier,
            gInfo,
            coherence,
            approved
        );

        return approved;
    }

    /**
     * @notice Atualiza thresholds G_info (só admin)
     */
    function updateGInfoThreshold(
        string calldata metric,
        uint256 newValue
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        bytes32 metricHash = keccak256(abi.encodePacked(metric));
        if (metricHash == keccak256("gInfoMin")) {
            emit GInfoThresholdUpdated("gInfoMin", gInfoMinThreshold, newValue);
            gInfoMinThreshold = newValue;
        } else if (metricHash == keccak256("coherenceMin")) {
            emit GInfoThresholdUpdated("coherenceMin", coherenceMinThreshold, newValue);
            coherenceMinThreshold = newValue;
        } else if (metricHash == keccak256("entropyMax")) {
            emit GInfoThresholdUpdated("entropyMax", entropyMaxThreshold, newValue);
            entropyMaxThreshold = newValue;
        } else {
            revert("Unknown metric");
        }
    }

    function isNullifierUsed(bytes32 nullifier) external view returns (bool) {
        return nullifierUsed[nullifier];
    }
}
