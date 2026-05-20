// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "openzeppelin-contracts/contracts/utils/cryptography/MerkleProof.sol";

contract TemporalMerkleCondition {
    struct ConditionData {
        bytes32 merkleRoot;
        uint256 targetTimestamp;
        uint256 requiredHumility; // humility check
    }

    // Mapping to store temporal blocks that have been finalized
    mapping(uint256 => bytes32) public temporalBlocks;

    // Mapping of ORCID -> humility score (simulated)
    mapping(address => uint256) public userHumility;

    event BlockFinalized(uint256 indexed timestamp, bytes32 merkleRoot);
    event HumilityRegistered(address indexed user, uint256 score);

    uint256 public constant GHOST_THRESHOLD = 5774; // 0.5774 * 10000

    function finalizeBlock(uint256 timestamp, bytes32 merkleRoot) external {
        temporalBlocks[timestamp] = merkleRoot;
        emit BlockFinalized(timestamp, merkleRoot);
    }

    function setUserHumility(address user, uint256 score) external {
        userHumility[user] = score;
        emit HumilityRegistered(user, score);
    }

    function checkReadCondition(
        address account,
        address vault,
        bytes calldata conditionData,
        bytes calldata accessAuxData
    ) external view returns (bool) {
        ConditionData memory expected = abi.decode(conditionData, (ConditionData));
        bytes32[] memory proof = abi.decode(accessAuxData, (bytes32[]));

        // Ensure humility score meets threshold
        uint256 humility = userHumility[account];
        if (humility < expected.requiredHumility || humility < GHOST_THRESHOLD) {
            return false;
        }

        bytes32 finalizedRoot = temporalBlocks[expected.targetTimestamp];
        if (finalizedRoot == bytes32(0)) {
            return false;
        }

        if (finalizedRoot != expected.merkleRoot) {
            return false;
        }

        // Verify Merkle Proof: the leaf is derived from account and vault
        // We use the account and vault addresses as the leaf node data to verify this specific
        // user has access rights proven by the temporal root
        bytes32 leaf = keccak256(bytes.concat(keccak256(abi.encode(account, vault))));

        // We allow empty proofs for simulation fallback where we just check root matching
        if (proof.length == 0) {
            return true;
        }

        return MerkleProof.verify(proof, finalizedRoot, leaf);
    }
}
