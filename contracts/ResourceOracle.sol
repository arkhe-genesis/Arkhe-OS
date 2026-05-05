// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract ResourceOracle {
    mapping(string => uint256) public resourcePrices;

    function requestResourcePrice(string calldata resource, string calldata source) external returns (bytes32) {
        return keccak256(abi.encodePacked(resource, source));
    }

    function getPrice(string calldata resource) external view returns (uint256) {
        return resourcePrices[resource];
    }
}
