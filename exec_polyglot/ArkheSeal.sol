// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract ArkheSeal {
    bytes32 public canonicalSeal;

    constructor(bytes32 _seal) {
        canonicalSeal = _seal;
    }

    function verifySeal(bytes32 _seal) public view returns (bool) {
        return _seal == canonicalSeal;
    }
}