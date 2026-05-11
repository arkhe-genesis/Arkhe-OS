// SPDX-License-Identifier: Cathedral-Sovereign-License
pragma solidity ^0.8.30;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";

interface IZK_ConsentVerifier {
    function verifyConsentCompliance(
        ConsentScope calldata scope,
        bytes32 operationCommitment,
        bytes calldata zkOperationProof
    ) external view returns (bool);
}

struct ConsentScope {
    bytes32 poolDid;           // Specific pool or wildcard (*)
    address tokenIn;           // Allowed input token
    address tokenOut;          // Allowed output token
    uint256 maxAmountIn;       // Maximum input limit
    uint256 maxSlippageBps;    // Maximum slippage in basis points
    uint256 validFrom;         // Start timestamp
    uint256 validUntil;        // Expiration timestamp
    bytes32 purposeHash;       // Hash of the purpose (e.g., "liquidity_provision")
}

/**
 * @title ConsentToken (Ω-NFT)
 * @notice Granular consent token for sovereign DEX operations.
 * Each Ω-NFT represents a cryptographic authorization with scope, limits, and expiration.
 */
contract ConsentToken is ERC721 {
    uint256 private _nextTokenId;

    mapping(uint256 => ConsentScope) public scopes;
    mapping(uint256 => bool) public consumed;  // Single-use tokens

    IZK_ConsentVerifier public zkVerifier;

    event ConsentTokenMinted(uint256 indexed tokenId, address indexed owner, bytes32 poolDid);
    event ConsentTokenConsumed(uint256 indexed tokenId, bytes32 operationCommitment);

    constructor(address _zkVerifier) ERC721("Cathedral Consent Token", "OMEGA") {
        zkVerifier = IZK_ConsentVerifier(_zkVerifier);
    }

    /**
     * @notice Creates a new ConsentToken with granular scope.
     */
    function mintConsent(
        address to,
        ConsentScope calldata scope
    ) external returns (uint256 tokenId) {
        tokenId = _nextTokenId++;
        _safeMint(to, tokenId);
        scopes[tokenId] = scope;
        emit ConsentTokenMinted(tokenId, to, scope.poolDid);
    }

    /**
     * @notice Validates and consumes a ConsentToken for an operation.
     * Requires ZK proof that the operation respects the scope.
     */
    function validateAndConsume(
        uint256 tokenId,
        bytes calldata zkOperationProof,
        bytes32 operationCommitment  // Commitment of the actual operation (swap/mint/burn)
    ) external returns (bool valid) {
        require(_ownerOf(tokenId) != address(0), "Token does not exist");
        require(!consumed[tokenId], "Consent already consumed");
        require(block.timestamp >= scopes[tokenId].validFrom, "Consent not yet valid");
        require(block.timestamp <= scopes[tokenId].validUntil, "Consent expired");

        // Verify ZK proof: the operation respects the consent scope
        require(
            zkVerifier.verifyConsentCompliance(
                scopes[tokenId],
                operationCommitment,
                zkOperationProof
            ),
            "Operation non-compliant with consent"
        );

        consumed[tokenId] = true;
        emit ConsentTokenConsumed(tokenId, operationCommitment);
        return true;
    }
}
