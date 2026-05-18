// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title ArkheTokenBridge
 * @notice Bridges Token Arkhe events to Ethereum as on‑chain seals
 * @dev Each seal is a SHA3‑256 hash anchored on‑chain with metadata
 */
contract ArkheTokenBridge {

    struct CanonicalSeal {
        bytes32 sealHash;
        string identity;
        string semantics;
        string payloadURI;       // IPFS or Arweave URI with full payload
        uint256 timestamp;
        address anchorer;         // Who anchored this seal
        uint256 phiCScore;        // Φ_C at time of sealing (0‑10000 bps)
    }

    mapping(bytes32 => CanonicalSeal) public seals;
    bytes32[] public sealHistory;

    event SealAnchored(bytes32 indexed sealHash, string identity, uint256 timestamp);

    address public arkheOracle;

    modifier onlyOracle() {
        require(msg.sender == arkheOracle, "Only Arkhe Oracle");
        _;
    }

    constructor(address _oracle) {
        arkheOracle = _oracle;
    }

    function anchorSeal(
        bytes32 _sealHash,
        string calldata _identity,
        string calldata _semantics,
        string calldata _payloadURI,
        uint256 _phiCScore
    ) external onlyOracle {
        require(seals[_sealHash].timestamp == 0, "Seal already anchored");

        seals[_sealHash] = CanonicalSeal({
            sealHash: _sealHash,
            identity: _identity,
            semantics: _semantics,
            payloadURI: _payloadURI,
            timestamp: block.timestamp,
            anchorer: msg.sender,
            phiCScore: _phiCScore
        });

        sealHistory.push(_sealHash);

        emit SealAnchored(_sealHash, _identity, block.timestamp);
    }

    function verifySeal(bytes32 _sealHash) external view returns (bool) {
        return seals[_sealHash].timestamp != 0;
    }

    function getSeal(bytes32 _sealHash) external view returns (CanonicalSeal memory) {
        return seals[_sealHash];
    }

    function getSealCount() external view returns (uint256) {
        return sealHistory.length;
    }
}