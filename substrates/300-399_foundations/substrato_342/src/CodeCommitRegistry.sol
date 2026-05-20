// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.28;

contract CodeCommitRegistry {
    // Basic implementation for testing purposes
    mapping(uint256 => uint256) public commitNonces;

    event CodeCommitted(
        uint256 indexed tokenId,
        string repoName,
        string commitHash,
        string ipfsCid,
        string[] fileCids,
        uint256 timestamp,
        uint256 nonce
    );

    function commitCode(
        uint256 tokenId,
        string memory repoName,
        string memory commitHash,
        string memory ipfsCid,
        string[] memory fileCids
    ) public {
        uint256 nonce = commitNonces[tokenId];
        emit CodeCommitted(tokenId, repoName, commitHash, ipfsCid, fileCids, block.timestamp, nonce);
        commitNonces[tokenId]++;
    }
}