// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title ArkheIdentity
 * @dev ERC-8004 inspired identity registry with ORCID + PQC public key binding
 */
contract ArkheIdentity {
    struct Identity {
        string orcid;
        bytes pqcPublicKey;
        uint256 reputation;
        bool isActive;
    }

    mapping(address => Identity) public identities;
    mapping(string => address) public orcidToAddress;
    mapping(address => bool) public authorizedCallers;

    event IdentityRegistered(address indexed agent, string orcid);
    event ReputationUpdated(address indexed agent, uint256 newReputation);
    event IdentityRevoked(address indexed agent);

    modifier onlyRegistered() {
        require(identities[msg.sender].isActive, "Identity not registered or inactive");
        _;
    }

    modifier onlyAuthorized() {
        require(authorizedCallers[msg.sender], "Caller is not authorized");
        _;
    }

    constructor() {
        // Deployer is initially authorized
        authorizedCallers[msg.sender] = true;
    }

    function setAuthorizedCaller(address caller, bool isAuthorized) external onlyAuthorized {
        authorizedCallers[caller] = isAuthorized;
    }

    function registerIdentity(string calldata orcid, bytes calldata pqcPublicKey) external {
        require(!identities[msg.sender].isActive, "Already registered");
        require(orcidToAddress[orcid] == address(0), "ORCID already in use");

        identities[msg.sender] = Identity({
            orcid: orcid,
            pqcPublicKey: pqcPublicKey,
            reputation: 0,
            isActive: true
        });
        orcidToAddress[orcid] = msg.sender;

        emit IdentityRegistered(msg.sender, orcid);
    }

    function updateReputation(address agent, uint256 delta, bool positive) external onlyAuthorized {
        require(identities[agent].isActive, "Agent not active");

        if (positive) {
            identities[agent].reputation += delta;
        } else {
            if (identities[agent].reputation >= delta) {
                identities[agent].reputation -= delta;
            } else {
                identities[agent].reputation = 0;
            }
        }

        emit ReputationUpdated(agent, identities[agent].reputation);
    }

    function revokeIdentity() external onlyRegistered {
        identities[msg.sender].isActive = false;
        // Optionally unbind ORCID
        emit IdentityRevoked(msg.sender);
    }
}
