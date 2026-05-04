// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title CosmicPoccVerifier
 * @dev Mock interface for ZK-proof verification of cosmic P_occ parameters.
 */
interface CosmicPoccVerifier {
    /**
     * @dev Verifies a ZK proof.
     * @param a Proof part A
     * @param b Proof part B
     * @param c Proof part C
     * @param input Public signals (commitment, etc.)
     * @return True if the proof is valid.
     */
    function verifyProof(
        uint[2] calldata a,
        uint[2][2] calldata b,
        uint[2] calldata c,
        uint[2] calldata input
    ) external view returns (bool);
}
