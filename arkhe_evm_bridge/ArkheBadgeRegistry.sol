// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title ArkheBadgeRegistry
 * @notice On-chain registry for ARKHE OS canonical seals and substrate attestations
 * @dev Integrates with TemporalChain for cross-chain verification
 */
contract ArkheBadgeRegistry {

    struct Badge {
        bytes signature;
        uint256 timestamp;
        address issuer;
        bool revoked;
    }

    // badgeKey => Badge
    mapping(bytes32 => Badge) public badges;

    // issuer => nonce (for replay protection)
    mapping(address => uint256) public nonces;

    // Authorized ARKHE oracles
    mapping(address => bool) public authorizedOracles;

    address public owner;

    event BadgeAnchored(
        bytes32 indexed badgeKey,
        address indexed issuer,
        uint256 timestamp,
        string substrateId
    );

    event BadgeRevoked(
        bytes32 indexed badgeKey,
        address indexed revoker,
        uint256 timestamp
    );

    event OracleAuthorized(address indexed oracle);
    event OracleDeauthorized(address indexed oracle);

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    modifier onlyOracle() {
        require(authorizedOracles[msg.sender], "Not authorized oracle");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    /**
     * @notice Anchor an ARKHE badge on-chain
     * @param badgeKey Deterministic key from substrate ID + seal + timestamp
     * @param signature ARKHE HSM-PQC or ECDSA signature
     */
    function anchorBadge(
        bytes32 badgeKey,
        bytes calldata signature
    ) external onlyOracle {
        require(badges[badgeKey].timestamp == 0, "Badge already exists");

        badges[badgeKey] = Badge({
            signature: signature,
            timestamp: block.timestamp,
            issuer: msg.sender,
            revoked: false
        });

        nonces[msg.sender]++;

        emit BadgeAnchored(badgeKey, msg.sender, block.timestamp, "");
    }

    /**
     * @notice Anchor badge with substrate metadata
     */
    function anchorBadgeWithMetadata(
        bytes32 badgeKey,
        bytes calldata signature,
        string calldata substrateId,
        bytes32 canonicalSeal,
        uint256 testCount,
        uint256 passCount
    ) external onlyOracle {
        require(badges[badgeKey].timestamp == 0, "Badge already exists");

        // Verify badge key matches metadata
        bytes32 expectedKey = keccak256(abi.encode(
            substrateId,
            canonicalSeal,
            block.timestamp
        ));
        require(expectedKey == badgeKey, "Invalid badge key");

        badges[badgeKey] = Badge({
            signature: signature,
            timestamp: block.timestamp,
            issuer: msg.sender,
            revoked: false
        });

        emit BadgeAnchored(badgeKey, msg.sender, block.timestamp, substrateId);
    }

    /**
     * @notice Verify badge exists and is valid
     */
    function verifyBadge(
        bytes32 badgeKey,
        bytes calldata signature
    ) external view returns (bool) {
        Badge memory badge = badges[badgeKey];
        if (badge.timestamp == 0 || badge.revoked) {
            return false;
        }

        // Compare signatures
        return keccak256(badge.signature) == keccak256(signature);
    }

    /**
     * @notice Get badge details
     */
    function getBadge(bytes32 badgeKey) external view returns (Badge memory) {
        return badges[badgeKey];
    }

    /**
     * @notice Revoke a badge (emergency only)
     */
    function revokeBadge(bytes32 badgeKey) external onlyOwner {
        require(badges[badgeKey].timestamp != 0, "Badge does not exist");
        badges[badgeKey].revoked = true;
        emit BadgeRevoked(badgeKey, msg.sender, block.timestamp);
    }

    // Oracle management
    function authorizeOracle(address oracle) external onlyOwner {
        authorizedOracles[oracle] = true;
        emit OracleAuthorized(oracle);
    }

    function deauthorizeOracle(address oracle) external onlyOwner {
        authorizedOracles[oracle] = false;
        emit OracleDeauthorized(oracle);
    }

    // Batch operations for gas efficiency
    function anchorBadgeBatch(
        bytes32[] calldata badgeKeys,
        bytes[] calldata signatures
    ) external onlyOracle {
        require(badgeKeys.length == signatures.length, "Length mismatch");

        for (uint i = 0; i < badgeKeys.length; i++) {
            if (badges[badgeKeys[i]].timestamp == 0) {
                badges[badgeKeys[i]] = Badge({
                    signature: signatures[i],
                    timestamp: block.timestamp,
                    issuer: msg.sender,
                    revoked: false
                });
                emit BadgeAnchored(badgeKeys[i], msg.sender, block.timestamp, "");
            }
        }
    }
}
