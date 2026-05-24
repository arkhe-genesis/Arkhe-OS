// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

interface IAIAgentVerification {
    function verifyAgent(address agent, string calldata orcid, bytes calldata proof) external returns (bool);
    function registerAgent(address agent, string calldata orcid, bytes calldata metadata) external;
}

/**
 * @title ArkheAgentVerification
 * @dev EIP-8126 logic for the formal validation of the Arkhe AI agents
 */
contract ArkheAgentVerification is IAIAgentVerification {
    struct AgentRecord {
        string orcid;
        bytes metadata;
        bool isVerified;
        uint256 verificationTimestamp;
    }

    mapping(address => AgentRecord) public agents;
    mapping(string => address) public orcidToAgent;

    address public verifierAuthority;

    event AgentRegistered(address indexed agent, string orcid);
    event AgentVerified(address indexed agent, string orcid, uint256 timestamp);

    modifier onlyVerifier() {
        require(msg.sender == verifierAuthority, "Only verifier authority");
        _;
    }

    constructor() {
        verifierAuthority = msg.sender;
    }

    function registerAgent(address agent, string calldata orcid, bytes calldata metadata) external override {
        require(bytes(agents[agent].orcid).length == 0, "Agent already registered");
        require(orcidToAgent[orcid] == address(0), "ORCID already registered");

        agents[agent] = AgentRecord({
            orcid: orcid,
            metadata: metadata,
            isVerified: false,
            verificationTimestamp: 0
        });

        orcidToAgent[orcid] = agent;

        emit AgentRegistered(agent, orcid);
    }

    function verifyAgent(address agent, string calldata orcid, bytes calldata proof) external override onlyVerifier returns (bool) {
        require(bytes(agents[agent].orcid).length > 0, "Agent not registered");
        require(keccak256(bytes(agents[agent].orcid)) == keccak256(bytes(orcid)), "ORCID mismatch");

        // ZKML/Formal Verification proof verification logic would go here
        // For now, we assume the proof is structurally correct as validated by the verifierAuthority

        agents[agent].isVerified = true;
        agents[agent].verificationTimestamp = block.timestamp;

        emit AgentVerified(agent, orcid, block.timestamp);

        return true;
    }

    function isAgentVerified(address agent) external view returns (bool) {
        return agents[agent].isVerified;
    }
}
