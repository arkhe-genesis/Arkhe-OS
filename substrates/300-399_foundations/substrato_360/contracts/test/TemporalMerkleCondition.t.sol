// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Test.sol";
import "../src/TemporalMerkleCondition.sol";
import "openzeppelin-contracts/contracts/utils/cryptography/MerkleProof.sol";

contract TemporalMerkleConditionTest is Test {
    TemporalMerkleCondition condition;

    address user1 = address(0x1);
    address vault = address(0x2);
    address user2 = address(0x4);

    function setUp() public {
        condition = new TemporalMerkleCondition();
        condition.setUserHumility(user1, 9000); // Pass Ghost
    }

    function _buildTree() internal view returns (bytes32 root, bytes32[] memory proof) {
        bytes32 leaf1 = keccak256(bytes.concat(keccak256(abi.encode(user1, vault))));
        bytes32 leaf2 = keccak256(bytes.concat(keccak256(abi.encode(user2, vault))));

        proof = new bytes32[](1);
        proof[0] = leaf2;

        if (leaf1 <= leaf2) {
            root = keccak256(abi.encodePacked(leaf1, leaf2));
        } else {
            root = keccak256(abi.encodePacked(leaf2, leaf1));
        }
    }

    function test_CheckReadCondition_PassesMultiLeaf() public {
        (bytes32 merkleRoot, bytes32[] memory proof) = _buildTree();
        uint256 targetTimestamp = 1000;

        condition.finalizeBlock(targetTimestamp, merkleRoot);

        bytes memory conditionData = abi.encode(
            TemporalMerkleCondition.ConditionData({
                merkleRoot: merkleRoot,
                targetTimestamp: targetTimestamp,
                requiredHumility: 6000 // Requires 0.60
            })
        );

        bytes memory accessAuxData = abi.encode(proof);

        bool result = condition.checkReadCondition(user1, vault, conditionData, accessAuxData);
        assertTrue(result);
    }

    function test_CheckReadCondition_PassesSingleLeaf() public {
        // Single leaf tree where root == leaf
        bytes32 leaf1 = keccak256(bytes.concat(keccak256(abi.encode(user1, vault))));
        bytes32 merkleRoot = leaf1;
        bytes32[] memory emptyProof = new bytes32[](0);

        uint256 targetTimestamp = 1000;
        condition.finalizeBlock(targetTimestamp, merkleRoot);

        bytes memory conditionData = abi.encode(
            TemporalMerkleCondition.ConditionData({
                merkleRoot: merkleRoot,
                targetTimestamp: targetTimestamp,
                requiredHumility: 6000
            })
        );

        bytes memory accessAuxData = abi.encode(emptyProof);

        bool result = condition.checkReadCondition(user1, vault, conditionData, accessAuxData);
        assertTrue(result);
    }

    function test_CheckReadCondition_FailsOnHumility() public {
        address arrogantUser = address(0x3);
        condition.setUserHumility(arrogantUser, 2000); // Below Ghost

        (bytes32 merkleRoot, bytes32[] memory proof) = _buildTree();
        uint256 targetTimestamp = 1000;

        condition.finalizeBlock(targetTimestamp, merkleRoot);

        bytes memory conditionData = abi.encode(
            TemporalMerkleCondition.ConditionData({
                merkleRoot: merkleRoot,
                targetTimestamp: targetTimestamp,
                requiredHumility: 6000
            })
        );

        bytes memory accessAuxData = abi.encode(proof);

        bool result = condition.checkReadCondition(arrogantUser, vault, conditionData, accessAuxData);
        assertFalse(result);
    }

    function test_CheckReadCondition_FailsOnInvalidSingleLeaf() public {
        // Trying to use single leaf approach with wrong user
        bytes32 leaf1 = keccak256(bytes.concat(keccak256(abi.encode(user2, vault)))); // root is user2's leaf
        bytes32 merkleRoot = leaf1;
        bytes32[] memory emptyProof = new bytes32[](0);

        uint256 targetTimestamp = 1000;
        condition.finalizeBlock(targetTimestamp, merkleRoot);

        bytes memory conditionData = abi.encode(
            TemporalMerkleCondition.ConditionData({
                merkleRoot: merkleRoot,
                targetTimestamp: targetTimestamp,
                requiredHumility: 6000
            })
        );

        bytes memory accessAuxData = abi.encode(emptyProof);

        // Try to access as user1, should fail because user1's leaf != user2's leaf
        bool result = condition.checkReadCondition(user1, vault, conditionData, accessAuxData);
        assertFalse(result);
    }
}
