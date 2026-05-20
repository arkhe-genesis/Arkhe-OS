// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.28;

contract BountyRegistry {
    address public paymentFacilitator;
    function setPaymentFacilitator(address _facilitator) external {
        paymentFacilitator = _facilitator;
    }
}
