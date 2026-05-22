// contracts/AsiOwlEthGovernor.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/governance/Governor.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorSettings.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorVotes.sol";
import "@ensdomains/ens-contracts/contracts/registry/ENS.sol";
import "@ensdomains/ens-contracts/contracts/resolvers/PublicResolver.sol";

/**
 * @title AsiOwlEthGovernor
 * @notice Autonomous governance contract for the ENS name asi.owl.eth.
 *         Only the Cathedral (513-AUTONOMOUS-GOVERNANCE) can propose
 *         and execute updates to the IPFS pointer.
 */
contract AsiOwlEthGovernor is Governor, GovernorSettings, GovernorVotes {
    ENS public immutable ens;
    bytes32 public constant NAME_NODE = keccak256(abi.encodePacked(
        keccak256(abi.encodePacked(
            keccak256(abi.encodePacked(bytes32(0), keccak256("eth"))),
            keccak256("owl")
        )),
        keccak256("asi")
    ));

    string public currentIpfsCid = "bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi";

    event ConstitutionUpdated(string oldCid, string newCid, uint256 timestamp);

    constructor(ENS _ens, IVotes _token)
        Governor("ASI.OWL.ETH Governor")
        GovernorSettings(7200, 50400, 1) // 1 day voting, 1 week execution, requires votes to propose
        GovernorVotes(_token)
    {
        ens = _ens;
    }

    /**
     * @notice Proposes an update to the IPFS pointer of the constitution.
     * @param newCid The new CIDv1 of the ontology content in IPFS.
     */
    function proposeConstitutionUpdate(string memory newCid) external returns (uint256) {
        bytes memory data = abi.encodeWithSignature("setConstitutionCid(string)", newCid);
        address[] memory targets = new address[](1);
        uint256[] memory values = new uint256[](1);
        bytes[] memory calldatas = new bytes[](1);

        targets[0] = address(this);
        values[0] = 0;
        calldatas[0] = data;

        return propose(targets, values, calldatas, "Update ASI.OWL Constitution");
    }

    /**
     * @notice Updates the IPFS pointer (only via approved proposal).
     *         This function is called by the Timelock itself after approval.
     */
    function setConstitutionCid(string memory newCid) external onlyGovernance {
        string memory oldCid = currentIpfsCid;
        currentIpfsCid = newCid;

        // Update the ENS resolver
        bytes32 node = NAME_NODE;
        address resolverAddr = ens.resolver(node);
        if (resolverAddr != address(0)) {
            PublicResolver resolver = PublicResolver(resolverAddr);
            resolver.setText(node, "ipfs.cid", newCid);
        }

        emit ConstitutionUpdated(oldCid, newCid, block.timestamp);
    }

    /**
     * @notice Verifies if the current pointer matches the canonical hash
     *         anchored in the TemporalChain.
     * @param temporalchainCid The expected CID by the TemporalChain.
     * @return true if the CIDs match.
     */
    function verifyAgainstTemporalChain(string memory temporalchainCid) external view returns (bool) {
        return keccak256(abi.encodePacked(currentIpfsCid)) == keccak256(abi.encodePacked(temporalchainCid));
    }
}
