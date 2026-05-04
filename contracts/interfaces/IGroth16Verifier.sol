// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @dev Interface para verificador Groth16 gerado por snarkjs
 * Nota: Esta interface deve corresponder ao contrato gerado por:
 *   snarkjs zkey export solidityverifier verification_key.zkey verifier.sol
 */
interface IGroth16Verifier {
    struct Groth16Proof {
        uint256[2] pi_a;
        uint256[2][2] pi_b;
        uint256[2] pi_c;
        uint256[] public_signals;
    }

    function verifyProof(
        uint256[2] calldata _pi_a,
        uint256[2][2] calldata _pi_b,
        uint256[2] calldata _pi_c,
        uint256[] calldata _public_signals
    ) external view returns (bool);
}
