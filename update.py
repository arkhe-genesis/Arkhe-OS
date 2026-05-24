import re

with open('substrates/632-EINSTEIN-ROSEN-TIME-MIRROR/substrato_632_time_mirror.py', 'r') as f:
    content = f.read()

new_sol = """// SPDX-License-Identifier: MIT
// ServRegistryBridge.sol — Substrates 631 + 632
// OpenServ Serv registry with Einstein-Rosen time mirror support
// Network: Ethereum-compatible (Polygon, Arbitrum, or L2)
// Author: ORCID 0009-0005-2697-4668
// Date: 2026-05-24

pragma solidity ^0.8.19;

contract ServRegistryBridge {
    // ── Enums ──────────────────────────────────────────────────────────
    enum ServStatus { Idle, Pending, Verified, Failed }
    enum ProofType { None, ZkML, TEE }
    enum TimeDirection { Forward, Backward }

    // ── Events ─────────────────────────────────────────────────────────
    event ServRegistered(
        bytes32 indexed servId,
        address indexed creator,
        string urlForward,
        string urlBackward,
        ProofType proofType,
        uint256 timestamp
    );

    event ServInvoked(
        bytes32 indexed servId,
        address indexed invoker,
        TimeDirection direction,
        bytes32 payloadHash,
        uint256 timestamp,
        uint256 latencyMs
    );

    event ProofVerified(
        bytes32 indexed servId,
        bytes32 indexed invocationId,
        bool valid,
        uint256 timestamp
    );

    event TimeMirrorFlipped(
        bytes32 indexed servId,
        TimeDirection newDirection,
        uint256 timestamp
    );

    event DualStateAnchored(
        bytes32 indexed forwardHash,
        bytes32 indexed backwardHash,
        bytes32 indexed dualHash,
        uint256 timestamp
    );

    // ── State ──────────────────────────────────────────────────────────
    struct Serv {
        bytes32 servId;
        address creator;
        string urlForward;
        string urlBackward;
        string vk;                    // verification key
        ProofType proofType;
        ServStatus status;
        uint256 registerTime;
        uint256 invokeCount;
        uint256 totalLatencyMs;
        uint256 verifiedCount;
        uint256 stake;
        bool active;
    }

    struct Invocation {
        bytes32 invocationId;
        bytes32 servId;
        address invoker;
        TimeDirection direction;
        bytes32 payloadHash;
        bytes32 resultHash;
        bool verified;
        uint256 latencyMs;
        uint256 timestamp;
    }

    mapping(bytes32 => Serv) public servs;
    mapping(bytes32 => bool) public knownServs;
    bytes32[] public servList;

    mapping(bytes32 => Invocation) public invocations;
    mapping(bytes32 => bytes32[]) public servInvocations;
    bytes32[] public invocationList;

    address public governance;
    uint256 public constant MIN_STAKE = 0.01 ether;
    uint256 public constant SERV_TIMEOUT_MS = 30000;
    uint256 public globalVerifiedCount;

    // ── Modifiers ──────────────────────────────────────────────────────
    modifier onlyGovernance() {
        require(msg.sender == governance, "631/632: not governance");
        _;
    }

    modifier validServ(bytes32 servId) {
        require(knownServs[servId], "631/632: unknown serv");
        _;
    }

    // ── Constructor ────────────────────────────────────────────────────
    constructor() {
        governance = msg.sender;
    }

    // ── Core Functions ─────────────────────────────────────────────────

    /**
     * @notice Register a new Serv
     * @param servId Unique identifier (SHA3-256 of metadata)
     * @param urlForward gRPC endpoint for tau+
     * @param urlBackward gRPC endpoint for tau-
     * @param vk Verification key (for zkML or TEE)
     * @param proofType Type of integrity proof required
     */
    function registerServ(
        bytes32 servId,
        string calldata urlForward,
        string calldata urlBackward,
        string calldata vk,
        ProofType proofType
    ) external payable {
        require(msg.value >= MIN_STAKE, "631/632: insufficient stake");
        require(!knownServs[servId], "631/632: serv already exists");
        require(bytes(urlForward).length > 0, "631/632: empty forward URL");
        require(bytes(urlBackward).length > 0, "631/632: empty backward URL");

        Serv memory s = Serv({
            servId: servId,
            creator: msg.sender,
            urlForward: urlForward,
            urlBackward: urlBackward,
            vk: vk,
            proofType: proofType,
            status: ServStatus.Idle,
            registerTime: block.timestamp,
            invokeCount: 0,
            totalLatencyMs: 0,
            verifiedCount: 0,
            stake: msg.value,
            active: true
        });

        servs[servId] = s;
        knownServs[servId] = true;
        servList.push(servId);

        emit ServRegistered(servId, msg.sender, urlForward, urlBackward, proofType, block.timestamp);
    }

    /**
     * @notice Record a Serv invocation (called by daemon after execution)
     * @param servId Serv identifier
     * @param direction Forward or Backward (time mirror)
     * @param payloadHash SHA3-256 of input payload
     * @param resultHash SHA3-256 of output result
     * @param latencyMs Execution latency in milliseconds
     */
    function recordInvocation(
        bytes32 servId,
        TimeDirection direction,
        bytes32 payloadHash,
        bytes32 resultHash,
        uint256 latencyMs
    ) external validServ(servId) {
        bytes32 invocationId = keccak256(abi.encodePacked(
            servId, msg.sender, payloadHash, block.timestamp
        ));

        Invocation memory inv = Invocation({
            invocationId: invocationId,
            servId: servId,
            invoker: msg.sender,
            direction: direction,
            payloadHash: payloadHash,
            resultHash: resultHash,
            verified: false,
            latencyMs: latencyMs,
            timestamp: block.timestamp
        });

        invocations[invocationId] = inv;
        servInvocations[servId].push(invocationId);
        invocationList.push(invocationId);
        servs[servId].invokeCount++;
        servs[servId].totalLatencyMs += latencyMs;

        emit ServInvoked(servId, msg.sender, direction, payloadHash, block.timestamp, latencyMs);
    }

    /**
     * @notice Verify an invocation proof
     * @param invocationId Invocation to verify
     * @param proofBytes Proof data (zkML proof or TEE attestation)
     */
    function verifyProof(
        bytes32 invocationId,
        bytes calldata proofBytes
    ) external onlyGovernance {
        require(invocations[invocationId].timestamp > 0, "631/632: unknown invocation");

        // In production: verify zk proof or TEE attestation
        bool valid = _verifyProofInternal(invocationId, proofBytes);
        if (valid && !invocations[invocationId].verified) {
            invocations[invocationId].verified = true;
            servs[invocations[invocationId].servId].verifiedCount++;
            globalVerifiedCount++;
        }

        emit ProofVerified(
            invocations[invocationId].servId,
            invocationId,
            valid,
            block.timestamp
        );
    }

    function _verifyProofInternal(bytes32 invocationId, bytes calldata proofBytes)
        internal pure returns (bool) {
        // Stub: real implementation would call verifier contract
        return proofBytes.length > 0;
    }

    /**
     * @notice Flip time direction for a Serv (Einstein-Rosen mirror)
     */
    function flipTimeMirror(bytes32 servId) external validServ(servId) {
        require(msg.sender == servs[servId].creator || msg.sender == governance,
                "631/632: not authorized");

        // Toggle direction in metadata (off-chain daemon reads this)
        emit TimeMirrorFlipped(servId,
            servs[servId].status == ServStatus.Idle ? TimeDirection.Backward : TimeDirection.Forward,
            block.timestamp);
    }

    /**
     * @notice Anchor dual-state (forward + backward) to Temporalchain
     */
    function anchorDualState(
        bytes32 forwardHash,
        bytes32 backwardHash
    ) external onlyGovernance {
        bytes32 dualHash = keccak256(abi.encodePacked(forwardHash, backwardHash));
        emit DualStateAnchored(forwardHash, backwardHash, dualHash, block.timestamp);
    }

    /**
     * @notice Deregister a Serv
     */
    function deregisterServ(bytes32 servId) external validServ(servId) {
        require(msg.sender == servs[servId].creator || msg.sender == governance,
                "631/632: not authorized");
        servs[servId].active = false;
    }

    /**
     * @notice Withdraw stake
     */
    function withdrawStake(bytes32 servId) external validServ(servId) {
        require(msg.sender == servs[servId].creator, "not authorized");
        require(!servs[servId].active, "must deregister first");
        uint256 amount = servs[servId].stake;
        require(amount > 0, "no stake to withdraw");
        servs[servId].stake = 0;
        payable(msg.sender).transfer(amount);
    }

    /**
     * @notice Get Serv statistics
     */
    function getServStats(bytes32 servId) external view validServ(servId) returns (
        uint256 invokeCount,
        uint256 avgLatency,
        uint256 verificationRate
    ) {
        Serv storage s = servs[servId];
        invokeCount = s.invokeCount;

        if (invokeCount == 0) {
            return (0, 0, 0);
        }

        avgLatency = s.totalLatencyMs / invokeCount;
        verificationRate = (s.verifiedCount * 100) / invokeCount;
    }

    /**
     * @notice Get global statistics
     */
    function getGlobalStats() external view returns (
        uint256 totalServs,
        uint256 totalInvocations,
        uint256 avgVerificationRate
    ) {
        totalServs = servList.length;
        totalInvocations = invocationList.length;

        if (totalInvocations == 0) {
            avgVerificationRate = 0;
        } else {
            avgVerificationRate = (globalVerifiedCount * 100) / totalInvocations;
        }
    }

    /**
     * @notice Update governance
     */
    function updateGovernance(address newGov) external onlyGovernance {
        governance = newGov;
    }

    // ── Fallback ───────────────────────────────────────────────────────
    receive() external payable {
        revert("631/632: direct deposits not allowed");
    }
}"""

# Use regex to replace the old SERV_REGISTRY_BRIDGE_SOL definition
content = re.sub(
    r'SERV_REGISTRY_BRIDGE_SOL = """(.*?)"""',
    f'SERV_REGISTRY_BRIDGE_SOL = """{new_sol}"""',
    content,
    flags=re.DOTALL
)

with open('substrates/632-EINSTEIN-ROSEN-TIME-MIRROR/substrato_632_time_mirror.py', 'w') as f:
    f.write(content)
