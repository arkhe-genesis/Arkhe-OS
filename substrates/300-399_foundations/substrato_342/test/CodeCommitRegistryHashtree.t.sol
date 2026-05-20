// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.28;

import "forge-std/Test.sol";
import "../src/CodeCommitRegistryHashtree.sol";

contract CodeCommitRegistryHashtreeTest is Test {
    CodeCommitRegistryHashtree public registry;
    address public user;
    uint256 public tokenId;

    function setUp() public {
        user = makeAddr("user");
        registry = new CodeCommitRegistryHashtree();
        tokenId = 1;
    }

    function testCommitCodeHashtree_EmitsEvent() public {
        string memory repoName = "arkhe-node";
        string memory commitHash = "abc123def456";
        string memory ipfsCid = "QmX7Y8Z9...";
        string[] memory fileNames = new string[](2);
        fileNames[0] = "main.py";
        fileNames[1] = "utils.py";

        bytes32[] memory fileHashes = new bytes32[](2);
        fileHashes[0] = keccak256(abi.encodePacked("code1"));
        fileHashes[1] = keccak256(abi.encodePacked("code2"));

        bytes32 merkleRoot = keccak256(abi.encodePacked("dummyRoot"));

        vm.expectEmit(true, true, true, true);
        emit CodeCommitRegistryHashtree.CodeCommitted(
            tokenId,
            repoName,
            commitHash,
            merkleRoot,
            block.timestamp,
            0 // nonce inicial
        );

        registry.commitCode(tokenId, repoName, commitHash, ipfsCid, merkleRoot, fileNames, fileHashes);
    }
}
