// SPDX-License-Identifier: Apache-2.0
// Arkhe OS — Substrato 375: OctraAgentRegistry
// Canon: ∞.Ω.∇+++.375.octra_agent_registry

pragma solidity ^0.8.28;

contract OctraAgentRegistry {
    struct OctraAgent {
        bytes32 agentId;
        address controller;
        address zkVerifier; // Endereço do verificador ZK do agente
        uint256 phiC;
        bool active;
    }

    mapping(bytes32 => OctraAgent) public agents;
    bytes32[] public agentList;

    event AgentRegistered(bytes32 indexed agentId, address controller, uint256 phiC);
    event AgentExecutionVerified(bytes32 indexed agentId, bytes32 proofHash);

    function registerAgent(
        bytes32 agentId,
        address zkVerifier,
        uint256 phiC
    ) external {
        require(phiC > 577350269189625764, "PhiC below Ghost");
        require(phiC < 999900000000000000, "PhiC above Gap");
        require(agents[agentId].agentId == bytes32(0), "Agent already registered");

        agents[agentId] = OctraAgent({
            agentId: agentId,
            controller: msg.sender,
            zkVerifier: zkVerifier,
            phiC: phiC,
            active: true
        });

        agentList.push(agentId);
        emit AgentRegistered(agentId, msg.sender, phiC);
    }

    function verifyExecution(
        bytes32 agentId,
        bytes calldata proof,
        bytes32[] calldata publicInputs
    ) external returns (bool) {
        OctraAgent storage agent = agents[agentId];
        require(agent.active, "Agent not active");

        // Delegar verificação ao verificador ZK do agente
        (bool ok, bytes memory result) = agent.zkVerifier.staticcall(
            abi.encodeWithSignature("verify(bytes,bytes32[])", proof, publicInputs)
        );
        require(ok, "ZK verifier call failed");
        bool valid = abi.decode(result, (bool));
        require(valid, "Invalid proof");

        emit AgentExecutionVerified(agentId, keccak256(proof));
        return true;
    }
}
