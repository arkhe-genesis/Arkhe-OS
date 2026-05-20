// SPDX-License-Identifier: Apache-2.0
// ═══════════════════════════════════════════════════════════════
// ARKHE OS — CODE COMMIT REGISTRY COM HASHTREE (Substrato 342)
// Canon: ∞.Ω.∇+++.342.code_commit_hashtree
// Cada commit inclui Merkle root + prova de inclusão para arquivos
// ═══════════════════════════════════════════════════════════════
pragma solidity ^0.8.28;

import "@openzeppelin/contracts/utils/cryptography/MerkleProof.sol";

interface IHashtreeVerifier {
    function verifyProof(
        bytes32 root,
        bytes32[] calldata proof,
        bytes32 leaf,
        uint256 index
    ) external pure returns (bool);
}

contract CodeCommitRegistryHashtree {
    using MerkleProof for bytes32[];

    struct Commit {
        uint256 authorTokenId;
        string repoName;
        string commitHash;
        string ipfsCid;              // Código completo no IPFS
        bytes32 merkleRoot;          // Raiz da árvore Merkle dos arquivos
        uint256 timestamp;
        uint256 nonce;
    }

    mapping(uint256 => Commit[]) public commitsByAuthor; // tokenId → [commits]

    event CodeCommitted(
        uint256 indexed authorTokenId,
        string repoName,
        string commitHash,
        bytes32 merkleRoot,
        uint256 timestamp,
        uint256 nonce
    );

    event FileVerified(
        uint256 indexed commitNonce,
        string fileName,
        bytes32 fileHash,
        bool verified
    );

    function commitCode(
        uint256 authorTokenId,
        string calldata repoName,
        string calldata commitHash,
        string calldata ipfsCid,
        bytes32 merkleRoot,
        string[] calldata fileNames,
        bytes32[] calldata fileHashes
    ) external {
        require(fileNames.length == fileHashes.length, "File arrays mismatch");

        uint256 nonce = commitsByAuthor[authorTokenId].length;

        commitsByAuthor[authorTokenId].push(Commit({
            authorTokenId: authorTokenId,
            repoName: repoName,
            commitHash: commitHash,
            ipfsCid: ipfsCid,
            merkleRoot: merkleRoot,
            timestamp: block.timestamp,
            nonce: nonce
        }));

        emit CodeCommitted(authorTokenId, repoName, commitHash, merkleRoot, block.timestamp, nonce);
    }

    function verifyFileInCommit(
        uint256 authorTokenId,
        uint256 commitNonce,
        string calldata fileName,
        bytes32 fileHash,
        bytes32[] calldata merkleProof
    ) external returns (bool) {
        Commit storage commit = commitsByAuthor[authorTokenId][commitNonce];

        // Verificar prova Merkle usando biblioteca OpenZeppelin
        bool valid = merkleProof.verify(commit.merkleRoot, fileHash);

        emit FileVerified(commitNonce, fileName, fileHash, valid);
        return valid;
    }

    function getCommitMerkleRoot(uint256 authorTokenId, uint256 commitNonce)
        external view returns (bytes32)
    {
        return commitsByAuthor[authorTokenId][commitNonce].merkleRoot;
    }
}
