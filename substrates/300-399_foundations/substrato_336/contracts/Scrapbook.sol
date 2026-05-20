// SPDX-License-Identifier: Apache-2.0
// ═══════════════════════════════════════════════════════════════
// ARKHE OS — SCRAPBOOK CONTRACT (Scraps On‑Chain)
// Canon: ∞.Ω.∇+++.336.scrapbook
// Cada scrap é um evento emitido, armazenado nos logs da EVM.
// Conteúdo grande é armazenado no IPFS; apenas o CID vai on‑chain.
// ═══════════════════════════════════════════════════════════════
pragma solidity ^0.8.28;

import "./ArkheIdentityNFT.sol";

contract Scrapbook {
    event ScrapSent(
        uint256 indexed fromTokenId,
        uint256 indexed toTokenId, // 0 = público
        string ipfsCid,           // conteúdo do scrap no IPFS
        string[] formulaCids,     // CIDs de fórmulas LaTeX
        uint256 timestamp,
        uint256 nonce
    );

    mapping(uint256 => uint256) public nonces; // tokenId -> nonce
    ArkheIdentityNFT public identityContract;

    constructor(address _identityContract) {
        identityContract = ArkheIdentityNFT(_identityContract);
    }

    function sendScrap(uint256 toTokenId, string calldata ipfsCid, string[] calldata formulaCids) external {
        uint256 fromTokenId = identityContract.tokenOfOwnerByIndex(msg.sender, 0);

        uint256 nonce = nonces[fromTokenId]++;
        emit ScrapSent(fromTokenId, toTokenId, ipfsCid, formulaCids, block.timestamp, nonce);
    }
}
