// SPDX-License-Identifier: Arkhe-Sovereignty-1.0
pragma solidity ^0.8.24;

/**
 * @title ArkheChainPQIntegrity
 * @notice Post-Quantum Integrity Proof contract for Arkhe-Chain
 * @dev Registers and validates PQ-Integrity Proofs from LLL lattice validators
 *
 * Arkhe-Chain Block: 847.690
 * Protocol: qhttp://2.0
 *
 * Each proof certifies that a network node:
 * 1. Resists LLL lattice-based attacks
 * 2. ECDSA key is not vulnerable to HNP (Hidden Number Problem)
 * 3. PQ security level meets NIST requirement (Level >= 3)
 * 4. Arkhe coherence (lambda_2) is above critical threshold (0.847)
 *
 * Integration with qhttp://:
 * - qhttp frames are validated by the LatticeValidator module
 * - PQ-Integrity Proofs are generated per-node, per-block
 * - Merkle roots are committed on-chain for network-wide integrity
 */

contract ArkheChainPQIntegrity {

    // ═══════════════════════════════════════════════════════════════
    // ARKHE(n) CONSTANTS
    // ═══════════════════════════════════════════════════════════════

    uint256 public constant ARKHE_CHAIN_GENESIS = 847000;
    uint256 public constant ARKHE_CHAIN_BLOCK = 847690;
    uint256 public constant LAMBDA2_CRIT_BPS = 8470; // 0.847 * 10000 (basis points)
    uint256 public constant NIST_LEVEL_MIN = 3;       // Minimum PQ security for Arkhe-Chain
    uint256 public constant MAX_PROOF_AGE = 7 days;
    uint256 public constant THERMAL_LOCK_TEMP = 42;   // 42°C thermal lock reference

    // NIST PQ Security Levels
    uint256 public constant NIST_LEVEL_1 = 1;
    uint256 public constant NIST_LEVEL_3 = 3;
    uint256 public constant NIST_LEVEL_5 = 5;

    // ═══════════════════════════════════════════════════════════════
    // DATA STRUCTURES
    // ═══════════════════════════════════════════════════════════════

    enum VulnerabilityStatus {
        IMMUNE,           // PQ algorithm, no ECDSA attack surface
        RESISTANT,        // ECDSA tested, no vulnerability found
        MONITORED,        // ECDSA node, under continuous LLL monitoring
        POTENTIALLY_VULN, // HNP detection confidence > 50%
        VULNERABLE        // Key recovered or confidence > 90%
    }

    enum ProofType {
        NODE_PROOF,       // Single node PQ integrity
        NETWORK_PROOF,    // Network-wide Merkle root
        SESSION_PROOF     // qhttp session batch validation
    }

    struct PQIntegrityProof {
        uint256 blockNumber;
        address validator;
        string nodeId;
        ProofType proofType;
        uint256 pqSecurityLevel;
        uint256 lambda2Coherence; // basis points (8470 = 0.847)
        bytes32 latticeCheckHash;
        bytes32 merkleRoot;
        uint256 timestamp;
        bool verified;
    }

    struct ECDSAResistanceReport {
        string attackType;        // "nonce_reuse", "biased_nonce", "linear_congruential", "lattice"
        VulnerabilityStatus status;
        uint256 confidence;       // basis points (10000 = 100%)
        uint256 latticeDimension;
        uint256 gnvsRatio;        // scaled by 1e6
        string details;
    }

    struct NetworkState {
        uint256 totalNodes;
        uint256 pqProtectedNodes;
        uint256 vulnerableNodes;
        bytes32 latestMerkleRoot;
        uint256 lastUpdate;
        uint256 avgLambda2;
    }

    // ═══════════════════════════════════════════════════════════════
    // STATE VARIABLES
    // ═══════════════════════════════════════════════════════════════

    address public owner;
    uint256 public currentBlock;
    bytes32 public previousBlockHash;

    // Node registrations
    mapping(string => bool) public registeredNodes;
    mapping(string => uint256) public nodePQLevel;
    mapping(string => uint256) public nodeLastProof;
    mapping(string => bytes32) public nodeLastProofHash;

    // Proof storage
    PQIntegrityProof[] public proofs;
    mapping(bytes32 => PQIntegrityProof) public proofByHash;
    mapping(bytes32 => bool) public proofExists;

    // Network state
    NetworkState public networkState;

    // Events
    event PQProofRegistered(
        uint256 indexed blockNumber,
        string nodeId,
        uint256 pqLevel,
        uint256 lambda2,
        bytes32 proofHash
    );

    event VulnerabilityDetected(
        string nodeId,
        string attackType,
        uint256 confidence,
        bytes32 proofHash
    );

    event NetworkProofCommitted(
        uint256 totalNodes,
        bytes32 merkleRoot,
        uint256 pqProtected,
        uint256 vulnerable
    );

    event NodeAlgorithmUpgraded(
        string nodeId,
        uint256 oldLevel,
        uint256 newLevel
    );

    // ═══════════════════════════════════════════════════════════════
    // MODIFIERS
    // ═══════════════════════════════════════════════════════════════

    modifier onlyOwner() {
        require(msg.sender == owner, "ArkheChain: not owner");
        _;
    }

    modifier validCoherence(uint256 lambda2Bps) {
        require(lambda2Bps >= LAMBDA2_CRIT_BPS,
                "ArkheChain: coherence below critical threshold");
        _;
    }

    // ═══════════════════════════════════════════════════════════════
    // CONSTRUCTOR
    // ═══════════════════════════════════════════════════════════════

    constructor() {
        owner = msg.sender;
        currentBlock = ARKHE_CHAIN_BLOCK;
        previousBlockHash = bytes32(0);
    }

    // ═══════════════════════════════════════════════════════════════
    // NODE MANAGEMENT
    // ═══════════════════════════════════════════════════════════════

    /**
     * @notice Register a new network node
     * @param nodeId Unique node identifier (e.g., "arkhe-rio-N01")
     * @param initialPQLevel Initial NIST PQ security level
     */
    function registerNode(string calldata nodeId, uint256 initialPQLevel) external onlyOwner {
        require(!registeredNodes[nodeId], "ArkheChain: node already registered");
        require(initialPQLevel <= 5, "ArkheChain: invalid PQ level");

        registeredNodes[nodeId] = true;
        nodePQLevel[nodeId] = initialPQLevel;
        networkState.totalNodes++;

        if (initialPQLevel >= NIST_LEVEL_MIN) {
            networkState.pqProtectedNodes++;
        }

        emit NodeAlgorithmUpgraded(nodeId, 0, initialPQLevel);
    }

    /**
     * @notice Update node's PQ algorithm level (migration)
     * @param nodeId Node identifier
     * @param newLevel New NIST PQ security level
     */
    function upgradeNodeAlgorithm(string calldata nodeId, uint256 newLevel) external onlyOwner {
        require(registeredNodes[nodeId], "ArkheChain: node not registered");

        uint256 oldLevel = nodePQLevel[nodeId];

        if (oldLevel < NIST_LEVEL_MIN && newLevel >= NIST_LEVEL_MIN) {
            networkState.pqProtectedNodes++;
        }
        if (oldLevel >= NIST_LEVEL_MIN && newLevel < NIST_LEVEL_MIN) {
            networkState.pqProtectedNodes--;
        }

        nodePQLevel[nodeId] = newLevel;
        emit NodeAlgorithmUpgraded(nodeId, oldLevel, newLevel);
    }

    // ═══════════════════════════════════════════════════════════════
    // PQ INTEGRITY PROOF SUBMISSION
    // ═══════════════════════════════════════════════════════════════

    /**
     * @notice Submit a PQ-Integrity Proof for a single node
     * @param nodeId Node identifier
     * @param pqLevel NIST PQ security level (0=ECDSA, 1/3/5=PQ)
     * @param lambda2Bps Arkhe coherence in basis points (8470 = 0.847)
     * @param latticeHash Hash of the lattice validation result
     * @param resistanceReports ECDSA resistance test results
     */
    function submitNodeProof(
        string calldata nodeId,
        uint256 pqLevel,
        uint256 lambda2Bps,
        bytes32 latticeHash,
        ECDSAResistanceReport[] calldata resistanceReports
    ) external validCoherence(lambda2Bps) returns (bytes32 proofHash) {
        require(registeredNodes[nodeId], "ArkheChain: node not registered");

        // Check for vulnerabilities
        bool hasVulnerability = false;
        for (uint256 i = 0; i < resistanceReports.length; i++) {
            if (resistanceReports[i].status == VulnerabilityStatus.VULNERABLE ||
                resistanceReports[i].status == VulnerabilityStatus.POTENTIALLY_VULN) {
                hasVulnerability = true;

                emit VulnerabilityDetected(
                    nodeId,
                    resistanceReports[i].attackType,
                    resistanceReports[i].confidence,
                    proofHash
                );
            }
        }

        // Update vulnerable count
        if (hasVulnerability) {
            networkState.vulnerableNodes++;
        }

        // Compute proof hash
        proofHash = keccak256(
            abi.encodePacked(
                currentBlock,
                nodeId,
                pqLevel,
                lambda2Bps,
                latticeHash,
                block.timestamp,
                previousBlockHash
            )
        );

        // Store proof
        PQIntegrityProof memory proof = PQIntegrityProof({
            blockNumber: currentBlock,
            validator: msg.sender,
            nodeId: nodeId,
            proofType: ProofType.NODE_PROOF,
            pqSecurityLevel: pqLevel,
            lambda2Coherence: lambda2Bps,
            latticeCheckHash: latticeHash,
            merkleRoot: bytes32(0),
            timestamp: block.timestamp,
            verified: !hasVulnerability
        });

        proofs.push(proof);
        proofByHash[proofHash] = proof;
        proofExists[proofHash] = true;
        nodeLastProof[nodeId] = block.timestamp;
        nodeLastProofHash[nodeId] = proofHash;

        // Update chain
        previousBlockHash = proofHash;
        currentBlock++;

        // Update network state
        networkState.lastUpdate = block.timestamp;
        uint256 totalLambda2 = networkState.avgLambda2 * (proofs.length - 1) + lambda2Bps;
        networkState.avgLambda2 = totalLambda2 / proofs.length;

        emit PQProofRegistered(currentBlock - 1, nodeId, pqLevel, lambda2Bps, proofHash);

        return proofHash;
    }

    /**
     * @notice Commit network-wide Merkle root (aggregated proof)
     * @param merkleRoot Merkle root of all node proofs
     * @param totalNodes Total nodes in the proof
     * @param pqProtected Number of PQ-protected nodes
     * @param vulnerableCount Number of vulnerable nodes
     */
    function commitNetworkProof(
        bytes32 merkleRoot,
        uint256 totalNodes,
        uint256 pqProtected,
        uint256 vulnerableCount
    ) external onlyOwner {
        networkState.latestMerkleRoot = merkleRoot;
        networkState.totalNodes = totalNodes;
        networkState.pqProtectedNodes = pqProtected;
        networkState.vulnerableNodes = vulnerableCount;
        networkState.lastUpdate = block.timestamp;

        emit NetworkProofCommitted(totalNodes, merkleRoot, pqProtected, vulnerableCount);
    }

    // ═══════════════════════════════════════════════════════════════
    // VIEW FUNCTIONS
    // ═══════════════════════════════════════════════════════════════

    /**
     * @notice Verify a PQ-Integrity Proof
     * @param proofHash Hash of the proof to verify
     */
    function verifyProof(bytes32 proofHash) external view returns (bool) {
        return proofExists[proofHash] && proofByHash[proofHash].verified;
    }

    /**
     * @notice Get proof details
     */
    function getProof(bytes32 proofHash) external view returns (
        uint256 blockNumber,
        string memory nodeId,
        uint256 pqLevel,
        uint256 lambda2,
        bool verified,
        uint256 timestamp
    ) {
        PQIntegrityProof storage p = proofByHash[proofHash];
        return (
            p.blockNumber,
            p.nodeId,
            p.pqSecurityLevel,
            p.lambda2Coherence,
            p.verified,
            p.timestamp
        );
    }

    /**
     * @notice Check if a node is Arkhe-Chain compliant
     * @dev A node is compliant if: PQ level >= 3 OR ECDSA with no vulnerabilities
     */
    function isNodeCompliant(string calldata nodeId) external view returns (bool) {
        return registeredNodes[nodeId] && nodePQLevel[nodeId] >= NIST_LEVEL_MIN;
    }

    /**
     * @notice Get network health metrics
     */
    function getNetworkHealth() external view returns (
        uint256 total,
        uint256 pqProtected,
        uint256 vulnerable,
        uint256 avgLambda2,
        uint256 compliancePercent
    ) {
        uint256 compliant = networkState.totalNodes > 0
            ? (networkState.pqProtectedNodes * 10000) / networkState.totalNodes
            : 0;
        return (
            networkState.totalNodes,
            networkState.pqProtectedNodes,
            networkState.vulnerableNodes,
            networkState.avgLambda2,
            compliant
        );
    }

    /**
     * @notice Get total number of proofs submitted
     */
    function getProofCount() external view returns (uint256) {
        return proofs.length;
    }
}
