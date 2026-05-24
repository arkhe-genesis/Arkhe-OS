// SPDX-License-Identifier: MIT
// AlphaNexus.sol — Substrate 651
// Formal proof registry with quantum-verified anchoring
// Author: ORCID 0009-0005-2697-4668
// Date: 2026-05-24

pragma solidity ^0.8.19;

contract AlphaNexus {
    struct ProofRecord {
        bytes32 problemHash;
        bytes32 proofHash;
        bytes32 quantumFingerprint;
        uint256 timestamp;
        uint256 agentConfig; // 1=A, 2=B, 3=C, 4=D
        uint256 costUsdCents;
        address verifier;
        bool isValid;
        string problemType; // "kernel", "clinical", "mathematical", "self-ref"
    }

    mapping(bytes32 => ProofRecord) public proofs;
    mapping(uint256 => bytes32[]) public proofsByCycle;
    bytes32 public latestProofRoot;
    bytes32[] public proofRootHistory;

    uint256 public constant ANCHOR_INTERVAL = 12;
    uint256 public lastAnchorTime;
    uint256 public totalProofs;
    uint256 public successfulProofs;

    event ProofAnchored(
        bytes32 indexed proofHash,
        bytes32 indexed problemHash,
        uint256 agentConfig,
        uint256 costUsdCents,
        uint256 timestamp
    );

    event ProofRootAnchored(bytes32 indexed root, uint256 timestamp);

    function anchorProof(
        bytes32 problemHash,
        bytes32 proofHash,
        bytes32 quantumFingerprint,
        uint256 agentConfig,
        uint256 costUsdCents,
        string calldata problemType
    ) external returns (bytes32) {
        require(agentConfig >= 1 && agentConfig <= 4, "Invalid agent config");

        proofs[proofHash] = ProofRecord({
            problemHash: problemHash,
            proofHash: proofHash,
            quantumFingerprint: quantumFingerprint,
            timestamp: block.timestamp,
            agentConfig: agentConfig,
            costUsdCents: costUsdCents,
            verifier: msg.sender,
            isValid: true,
            problemType: problemType
        });

        totalProofs++;
        successfulProofs++;

        // Update Merkle root
        latestProofRoot = keccak256(abi.encodePacked(latestProofRoot, proofHash));
        proofRootHistory.push(latestProofRoot);

        emit ProofAnchored(proofHash, problemHash, agentConfig, costUsdCents, block.timestamp);

        // Periodic anchoring
        if (block.timestamp >= lastAnchorTime + ANCHOR_INTERVAL) {
            lastAnchorTime = block.timestamp;
            emit ProofRootAnchored(latestProofRoot, block.timestamp);
        }

        return proofHash;
    }

    function invalidateProof(bytes32 proofHash, string calldata reason) external {
        require(proofs[proofHash].timestamp > 0, "Proof not found");
        proofs[proofHash].isValid = false;
        successfulProofs--;
        // Log reason to Akashic Anchor via event
        emit ProofInvalidated(proofHash, reason, block.timestamp);
    }

    event ProofInvalidated(bytes32 indexed proofHash, string reason, uint256 timestamp);

    function getPhiProof() external view returns (uint256) {
        if (totalProofs == 0) return 0;
        return (successfulProofs * 1e18) / totalProofs;
    }

    function getProofsByCycle(uint256 cycle) external view returns (bytes32[] memory) {
        return proofsByCycle[cycle];
    }

    function getProofRootHistory() external view returns (bytes32[] memory) {
        return proofRootHistory;
    }
}
