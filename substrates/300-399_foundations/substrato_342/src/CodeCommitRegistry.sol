// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.28;

contract CodeCommitRegistry {
    struct Commit {
        uint256 authorTokenId;
        string repoName;
        string commitHash;
        string ipfsCid;
        string[] fileCids;
        uint256 timestamp;
        uint256 nonce;
    }

    mapping(uint256 => uint256) public commitNonces;
    mapping(uint256 => Commit[]) public commitsByAuthor;

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

        commitsByAuthor[tokenId].push(Commit({
            authorTokenId: tokenId,
            repoName: repoName,
            commitHash: commitHash,
            ipfsCid: ipfsCid,
            fileCids: fileCids,
            timestamp: block.timestamp,
            nonce: nonce
        }));

        emit CodeCommitted(tokenId, repoName, commitHash, ipfsCid, fileCids, block.timestamp, nonce);
        commitNonces[tokenId]++;
    }
}
