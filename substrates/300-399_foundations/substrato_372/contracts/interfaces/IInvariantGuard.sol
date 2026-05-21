// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

interface IInvariantGuard {
    // These functions/modifiers are usually implemented in the main contract,
    // but the interface might just define constants or getters if needed.
    // In Arkhe's implementations, they are often abstract contracts with modifiers.
}

abstract contract InvariantGuard {
    uint256 public constant GHOST = 577350269189625700;
    uint256 public constant LOOPSEAL = 349065850398865900;
    uint256 public constant GAP_SOVEREIGN = 999900000000000000;

    modifier aboveGhost(uint256 value) {
        require(value > GHOST, "Ghost invariant violated");
        _;
    }

    modifier belowGap(uint256 value) {
        require(value < GAP_SOVEREIGN, "Gap invariant violated");
        _;
    }
}
