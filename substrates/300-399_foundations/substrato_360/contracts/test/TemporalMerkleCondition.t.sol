// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Test.sol";
import "../src/TemporalMerkleCondition.sol";
import "openzeppelin-contracts/contracts/utils/cryptography/MerkleProof.sol";

contract TemporalMerkleConditionTest is Test {
    TemporalMerkleCondition condition;

    address user1 = address(0x1);
    address vault = address(0x2);

    function setUp() public {
        condition = new TemporalMerkleCondition();
        condition.setUserHumility(user1, 9000); // Pass Ghost
    }

    function test_CheckReadCondition_Passes() public {
        uint256 targetTimestamp = 1000;
        bytes32 merkleRoot = keccak256("test_root");

        condition.finalizeBlock(targetTimestamp, merkleRoot);

        bytes memory conditionData = abi.encode(
            TemporalMerkleCondition.ConditionData({
                merkleRoot: merkleRoot,
                targetTimestamp: targetTimestamp,
                requiredHumility: 6000 // Requires 0.60
            })
        );

        bytes32[] memory emptyProof = new bytes32[](0);
        bytes memory accessAuxData = abi.encode(emptyProof);

        bool result = condition.checkReadCondition(user1, vault, conditionData, accessAuxData);
        assertTrue(result);
    }

    function test_CheckReadCondition_FailsOnHumility() public {
        address arrogantUser = address(0x3);
        condition.setUserHumility(arrogantUser, 2000); // Below Ghost

        uint256 targetTimestamp = 1000;
        bytes32 merkleRoot = keccak256("test_root");

        condition.finalizeBlock(targetTimestamp, merkleRoot);

        bytes memory conditionData = abi.encode(
            TemporalMerkleCondition.ConditionData({
                merkleRoot: merkleRoot,
                targetTimestamp: targetTimestamp,
                requiredHumility: 6000
            })
        );

        bytes32[] memory emptyProof = new bytes32[](0);
        bytes memory accessAuxData = abi.encode(emptyProof);

        bool result = condition.checkReadCondition(arrogantUser, vault, conditionData, accessAuxData);
        assertFalse(result);
    }

    function test_CheckReadCondition_WithRealProof() public {
        // Construct a small 2-leaf Merkle Tree
        bytes32 leaf1 = keccak256(bytes.concat(keccak256(abi.encode(user1, vault))));

        address user2 = address(0x4);
        bytes32 leaf2 = keccak256(bytes.concat(keccak256(abi.encode(user2, vault))));

        bytes32[] memory proof = new bytes32[](1);
        proof[0] = leaf2;

        // Sorting siblings as per OpenZeppelin MerkleProof standard
        bytes32 root;
        if (leaf1 <= leaf2) {
            root = keccak256(abi.encodePacked(leaf1, leaf2));
        } else {
            root = keccak256(abi.encodePacked(leaf2, leaf1));
        }

        uint256 targetTimestamp = 2000;
        condition.finalizeBlock(targetTimestamp, root);

        bytes memory conditionData = abi.encode(
            TemporalMerkleCondition.ConditionData({
                merkleRoot: root,
                targetTimestamp: targetTimestamp,
                requiredHumility: 6000
            })
        );

        bytes memory accessAuxData = abi.encode(proof);

        bool result = condition.checkReadCondition(user1, vault, conditionData, accessAuxData);
        assertTrue(result);
    }
}
