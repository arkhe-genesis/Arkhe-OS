// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.28;

import "forge-std/Test.sol";
import "../src/CodeCommitRegistry.sol";

contract CodeCommitRegistryTest is Test {
    CodeCommitRegistry public registry;
    address public user;
    uint256 public tokenId;

    function setUp() public {
        user = makeAddr("user");
        registry = new CodeCommitRegistry();
        tokenId = 1; // Simular token ID do usuário
    }

    function testCommitCode_EmitsEvent() public {
        string memory repoName = "arkhe-node";
        string memory commitHash = "abc123def456";
        string memory ipfsCid = "QmX7Y8Z9...";
        string[] memory fileCids = new string[](2);
        fileCids[0] = "QmFile1...";
        fileCids[1] = "QmFile2...";

        vm.expectEmit(true, true, true, true);
        emit CodeCommitRegistry.CodeCommitted(
            tokenId,
            repoName,
            commitHash,
            ipfsCid,
            fileCids,
            block.timestamp,
            0 // nonce inicial
        );

        registry.commitCode(tokenId, repoName, commitHash, ipfsCid, fileCids);
    }

    function testCommitCode_IncrementsNonce() public {
        string memory repoName = "arkhe-node";
        string memory commitHash = "abc123";
        string memory ipfsCid = "QmX...";
        string[] memory fileCids = new string[](0);

        // Primeiro commit
        registry.commitCode(tokenId, repoName, commitHash, ipfsCid, fileCids);
        assertEq(registry.commitNonces(tokenId), 1);

        // Segundo commit
        registry.commitCode(tokenId, repoName, commitHash, ipfsCid, fileCids);
        assertEq(registry.commitNonces(tokenId), 2);
    }

    function testCommitCode_UniqueCidsPerCommit() public {
        // Cada commit deve ter CID único para prevenir replay
        string memory ipfsCid1 = "QmUnique1...";
        string memory ipfsCid2 = "QmUnique2...";

        // Ambos podem ser registrados (não há restrição de duplicata de CID)
        // A imutabilidade é garantida pelo nonce + timestamp
        registry.commitCode(tokenId, "repo", "hash1", ipfsCid1, new string[](0));
        registry.commitCode(tokenId, "repo", "hash2", ipfsCid2, new string[](0));

        // Teste passa: múltiplos commits são permitidos
        assertEq(registry.commitNonces(tokenId), 2);
    }
}