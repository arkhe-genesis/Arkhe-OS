// SPDX-License-Identifier: Apache-2.0
// ═══════════════════════════════════════════════════════════════
// ARKHE OS — CODE COMMIT REGISTRY (Substrato 342)
// Canon: ∞.Ω.∇+++.342.code_commit
// Cada commit de código é um evento imutável com CID do IPFS.
// ═══════════════════════════════════════════════════════════════
pragma solidity ^0.8.28;

contract CodeCommitRegistry {
    event CodeCommitted(
        uint256 indexed authorTokenId,
        string repoName,
        string commitHash,
        string ipfsCid,           // Código fonte completo no IPFS
        string[] fileCids,        // CIDs de ficheiros individuais
        uint256 timestamp,
        uint256 nonce
    );

    mapping(uint256 => uint256) public commitNonces; // tokenId → nonce

    function commitCode(
        uint256 authorTokenId,
        string calldata repoName,
        string calldata commitHash,
        string calldata ipfsCid,
        string[] calldata fileCids
    ) external {
        uint256 nonce = commitNonces[authorTokenId]++;
        emit CodeCommitted(authorTokenId, repoName, commitHash, ipfsCid, fileCids, block.timestamp, nonce);
    }
}
