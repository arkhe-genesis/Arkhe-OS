// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title KnowledgeAsset
 * @dev Contract for anchoring ethical syntheses and other knowledge assets on the Arkhe-Block L2.
 * Based on the Merkabah-QNC architecture.
 */
contract KnowledgeAsset is ERC721URIStorage, Ownable {
    uint256 private _nextTokenId;

    struct Metadata {
        address creator;
        uint256 vroScore; // Scale 1e18 = 1.0
        uint256 timestamp;
    }

    mapping(uint256 => Metadata) public assetMetadata;

    event KnowledgeAnchored(
        uint256 indexed tokenId,
        address indexed creator,
        string metadataUri,
        uint256 vroScore
    );

    constructor(address initialOwner)
        ERC721("Arkhe Knowledge Asset", "AKA")
        Ownable(initialOwner)
    {}

    /**
     * @dev Mints a new Knowledge Asset representing an ethical synthesis or discovery.
     * @param creator The address of the entity that created the synthesis (e.g., MERKABAH).
     * @param metadataUri The URI to the full metadata/state of the synthesis.
     * @param vroScore The fidelity score from the Vector Reputation Oracle.
     */
    function mint(
        address creator,
        string memory metadataUri,
        uint256 vroScore
    ) public onlyOwner returns (uint256) {
        uint256 tokenId = _nextTokenId++;

        _safeMint(creator, tokenId);
        _setTokenURI(tokenId, metadataUri);

        assetMetadata[tokenId] = Metadata({
            creator: creator,
            vroScore: vroScore,
            timestamp: block.timestamp
        });

        emit KnowledgeAnchored(tokenId, creator, metadataUri, vroScore);

        return tokenId;
    }

    /**
     * @dev Returns the metadata for a given token ID.
     */
    function getMetadata(uint256 tokenId) public view returns (Metadata memory) {
        require(_ownerOf(tokenId) != address(0), "Asset does not exist");
        return assetMetadata[tokenId];
    }
}
