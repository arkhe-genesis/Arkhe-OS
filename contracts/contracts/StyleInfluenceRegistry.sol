// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title ARKHE Style Influence Registry
 * @notice Registra fingerprints artísticos e relações de influência on-chain.
 * @dev Otimizado para gas com suporte a batch operations.
 */
contract StyleInfluenceRegistry {

    struct ArtFingerprint {
        address owner;
        bytes32 perceptualHash;
        bytes32 styleHash;
        string uri;
        uint40 timestamp;
        uint64 totalInfluence;
        uint64 totalRoyalties;
        bool exists;
    }

    struct InfluenceRecord {
        bytes32 sourceFingerprint;
        bytes32 targetFingerprint;
        bytes32 proofHash;
        uint256 similarity;
        uint40 timestamp;
        bool verified;
    }

    mapping(bytes32 => ArtFingerprint) public fingerprints;
    mapping(bytes32 => InfluenceRecord[]) public influencesReceived;
    mapping(bytes32 => InfluenceRecord[]) public influencesExerted;
    mapping(address => bytes32[]) public artistWorks;

    uint256 public totalFingerprints;
    uint256 public totalInfluences;
    uint256 public minInfluenceThreshold;
    address public escrowContract;

    error AlreadyRegistered();
    error NotRegistered();
    error SelfReference();
    error BelowThreshold();
    error ZeroAddress();

    event FingerprintRegistered(bytes32 indexed fingerprint, address indexed owner, uint256 timestamp);
    event InfluenceRecorded(bytes32 indexed source, bytes32 indexed target, uint256 similarity, bytes32 proofHash);
    event RoyaltyClaimed(bytes32 indexed fingerprint, address indexed owner, uint256 amount);
    event EscrowUpdated(address indexed newEscrow);

    modifier fingerprintExists(bytes32 fp) {
        if (!fingerprints[fp].exists) revert NotRegistered();
        _;
    }

    constructor(uint256 _minInfluenceThreshold) {
        minInfluenceThreshold = _minInfluenceThreshold > 0 ? _minInfluenceThreshold : 32768;
    }

    function registerFingerprint(
        bytes32 perceptualHash,
        bytes32 styleHash,
        string calldata uri
    ) public returns (bytes32 fingerprint) {
        fingerprint = keccak256(abi.encodePacked(msg.sender, perceptualHash, styleHash));
        if (fingerprints[fingerprint].exists) revert AlreadyRegistered();

        fingerprints[fingerprint] = ArtFingerprint({
            owner: msg.sender,
            perceptualHash: perceptualHash,
            styleHash: styleHash,
            uri: uri,
            timestamp: uint40(block.timestamp),
            totalInfluence: 0,
            totalRoyalties: 0,
            exists: true
        });

        artistWorks[msg.sender].push(fingerprint);
        totalFingerprints++;

        emit FingerprintRegistered(fingerprint, msg.sender, block.timestamp);
    }

    function registerBatch(
        bytes32[] calldata perceptualHashes,
        bytes32[] calldata styleHashes,
        string[] calldata uris
    ) external returns (bytes32[] memory fingerprints_) {
        uint256 len = perceptualHashes.length;
        require(len == styleHashes.length && len == uris.length, "Array length mismatch");
        require(len > 0 && len <= 256, "Batch size 1-256");

        fingerprints_ = new bytes32[](len);
        for (uint256 i; i < len;) {
            fingerprints_[i] = registerFingerprint(perceptualHashes[i], styleHashes[i], uris[i]);
            unchecked { ++i; }
        }
    }

    function recordInfluence(
        bytes32 sourceFingerprint,
        bytes32 targetFingerprint,
        bytes32 proofHash
    ) public fingerprintExists(sourceFingerprint) fingerprintExists(targetFingerprint) {
        if (sourceFingerprint == targetFingerprint) revert SelfReference();

        uint256 sim = _calculateSimilarity(
            fingerprints[sourceFingerprint].styleHash,
            fingerprints[targetFingerprint].styleHash
        );

        if (sim < minInfluenceThreshold) revert BelowThreshold();

        influencesReceived[targetFingerprint].push(InfluenceRecord({
            sourceFingerprint: sourceFingerprint,
            targetFingerprint: targetFingerprint,
            proofHash: proofHash,
            similarity: sim,
            timestamp: uint40(block.timestamp),
            verified: proofHash != bytes32(0)
        }));

        influencesExerted[sourceFingerprint].push(InfluenceRecord({
            sourceFingerprint: sourceFingerprint,
            targetFingerprint: targetFingerprint,
            proofHash: proofHash,
            similarity: sim,
            timestamp: uint40(block.timestamp),
            verified: proofHash != bytes32(0)
        }));

        totalInfluences++;
        unchecked {
            fingerprints[sourceFingerprint].totalInfluence += uint64(sim);
        }

        emit InfluenceRecorded(sourceFingerprint, targetFingerprint, sim, proofHash);
    }

    function recordBatchInfluence(
        bytes32[] calldata sources,
        bytes32[] calldata targets,
        bytes32[] calldata proofs
    ) external {
        uint256 len = sources.length;
        require(len == targets.length && len == proofs.length, "Array mismatch");
        require(len > 0 && len <= 256, "Batch size 1-256");

        for (uint256 i; i < len;) {
            recordInfluence(sources[i], targets[i], proofs[i]);
            unchecked { ++i; }
        }
    }

    function _calculateSimilarity(bytes32 styleA, bytes32 styleB) internal pure returns (uint256) {
        // Euclidean distance-based similarity in Q16.16 fixed point
        int256 diff = int256(uint256(styleA)) - int256(uint256(styleB));
        uint256 squared = uint256(diff * diff);

        // Normalize: closer values → higher similarity
        // Max similarity (squared=0): 65536 (1.0 in Q16.16)
        // Approx max squared: ~2^256, map to ~0

        // Use a sigmoid-like curve for better distribution
        if (squared == 0) return 65536; // identical

        // Heuristic: similarity = 65536 / (1 + squared_normalized)
        // Shift squared right to get a manageable number
        uint256 normalized = squared >> 224; // ~16 bits
        if (normalized >= 65536) return 0;

        return 65536 / (1 + normalized);
    }

    function setEscrow(address _escrow) external {
        if (_escrow == address(0)) revert ZeroAddress();
        escrowContract = _escrow;
        emit EscrowUpdated(_escrow);
    }

    function setMinThreshold(uint256 _threshold) external {
        if (escrowContract == address(0)) revert ZeroAddress();
        minInfluenceThreshold = _threshold;
    }
}
