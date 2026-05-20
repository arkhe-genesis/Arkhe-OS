// SPDX-License-Identifier: Apache-2.0
// Substrato 360 — SGX Attestation Whitelist
pragma solidity ^0.8.28;

import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title SGXAttestationWhitelist
 * @notice Gerencia whitelist de MRENCLAVE/MRSIGNER para validadores DKG.
 *         Selos canônicos whitelist: 260, 261, 263.
 */
contract SGXAttestationWhitelist is Ownable {
    struct EnclaveIdentity {
        bytes32 mrenclave;   // Hash do enclave
        bytes32 mrsigner;    // Hash do signer
        uint16 svn;          // Security Version Number
        bool active;
    }

    mapping(bytes32 => EnclaveIdentity) public enclaves;
    uint256[] public canonicalSeals = [260, 261, 263];

    event EnclaveRegistered(bytes32 indexed mrenclave, uint256 indexed seal);
    event EnclaveRevoked(bytes32 indexed mrenclave);

    function registerEnclave(
        bytes32 mrenclave,
        bytes32 mrsigner,
        uint16 svn,
        uint256 canonicalSeal
    ) external onlyOwner {
        require(_isCanonicalSeal(canonicalSeal), "Seal not in canonical whitelist");
        require(svn >= 4, "SVN below minimum");

        enclaves[mrenclave] = EnclaveIdentity({
            mrenclave: mrenclave,
            mrsigner: mrsigner,
            svn: svn,
            active: true
        });

        emit EnclaveRegistered(mrenclave, canonicalSeal);
    }

    function verifyEnclave(bytes32 mrenclave) external view returns (bool) {
        EnclaveIdentity storage enclave = enclaves[mrenclave];
        return enclave.active;
    }

    function _isCanonicalSeal(uint256 seal) internal view returns (bool) {
        for (uint256 i = 0; i < canonicalSeals.length; i++) {
            if (canonicalSeals[i] == seal) return true;
        }
        return false;
    }
}
