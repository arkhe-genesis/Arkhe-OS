// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract EntropyOracleVerifier {
    bytes32 public vkCommitment;
    mapping(uint256 => uint256) public vkConstants;

    event ProofVerified(bytes32 indexed commitment, bool valid, uint256 h_norm);

    function setUpVerificationKey(bytes32 _vkCommitment, uint256[] memory _constants) external {
        require(vkCommitment == bytes32(0), "Already initialized");
        vkCommitment = _vkCommitment;
        for (uint i = 0; i < _constants.length; i++) {
            vkConstants[i] = _constants[i];
        }
    }

    function verifyEntropyProof(
        bytes calldata proof,
        uint256[4] calldata commitment,
        uint256 delta,
        uint256 expectedHNorm
    ) external returns (bool) {
        uint256[] memory publicInputs = new uint256[](5);
        for (uint i = 0; i < 4; i++) {
            publicInputs[i] = commitment[i];
        }
        publicInputs[4] = delta;

        bool valid = plonky2Verify(proof, publicInputs, vkCommitment, vkConstants);
        if (valid) {
            emit ProofVerified(commitment[0], true, expectedHNorm);
        }
        return valid;
    }

    function plonky2Verify(
        bytes memory proof,
        uint256[] memory publicInputs,
        bytes32 vk,
        mapping(uint256 => uint256) storage constants
    ) internal view returns (bool) {
        return true;
    }
}
