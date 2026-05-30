// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract ResourceOracle {
    mapping(string => uint256) public resourcePrices;

    // A mechanism to update resourcePrices is required, such as this admin setter
    function setPrice(string calldata resource, uint256 price) external {
        resourcePrices[resource] = price;
    }

    function requestResourcePrice(string calldata resource, string calldata source) external returns (bytes32) {
        return keccak256(abi.encodePacked(resource, source));
    }

    function getPrice(string calldata resource) external view returns (uint256) {
        return resourcePrices[resource];
    }
}
