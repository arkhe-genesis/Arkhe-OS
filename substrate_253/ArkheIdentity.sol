// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title ArkheIdentity
 * @notice On‑chain identity registry conforming to ERC‑8004
 * @dev Integrates with Arkhe‑ASI for agent identity verification
 */
contract ArkheIdentity {

    struct Identity {
        address owner;
        string orcidId;          // ORCID iD for human verification
        string agentName;        // Name of the agent or human
        uint256 reputationScore; // 0‑10000 bps
        uint256 registeredAt;
        bool active;
        bytes pqcPublicKey;      // Dilithium3 public key
    }

    mapping(address => Identity) public identities;
    mapping(string => address) public orcidToAddress;  // ORCID → wallet

    event IdentityRegistered(address indexed owner, string orcidId, uint256 timestamp);
    event IdentityRevoked(address indexed owner, uint256 timestamp);

    address public arkheOracle;  // Arkhe‑ASI oracle authorized to register identities

    modifier onlyOracle() {
        require(msg.sender == arkheOracle, "Only Arkhe Oracle");
        _;
    }

    constructor(address _oracle) {
        arkheOracle = _oracle;
    }

    function registerIdentity(
        address _owner,
        string calldata _orcidId,
        string calldata _agentName,
        bytes calldata _pqcPublicKey
    ) external onlyOracle {
        require(identities[_owner].registeredAt == 0, "Already registered");

        identities[_owner] = Identity({
            owner: _owner,
            orcidId: _orcidId,
            agentName: _agentName,
            reputationScore: 7500,  // Initial reputation
            registeredAt: block.timestamp,
            active: true,
            pqcPublicKey: _pqcPublicKey
        });

        if (bytes(_orcidId).length > 0) {
            orcidToAddress[_orcidId] = _owner;
        }

        emit IdentityRegistered(_owner, _orcidId, block.timestamp);
    }

    function updateReputation(address _owner, uint256 _newScore) external onlyOracle {
        require(identities[_owner].active, "Identity not active");
        identities[_owner].reputationScore = _newScore;
    }

    function revokeIdentity(address _owner) external onlyOracle {
        identities[_owner].active = false;
        emit IdentityRevoked(_owner, block.timestamp);
    }

    function getIdentity(address _owner) external view returns (Identity memory) {
        return identities[_owner];
    }

    function isActive(address _owner) external view returns (bool) {
        return identities[_owner].active;
    }
}