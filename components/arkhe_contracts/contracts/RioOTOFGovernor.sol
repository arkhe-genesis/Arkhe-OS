// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/governance/Governor.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorSettings.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorVotes.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorTimelockControl.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorCountingSimple.sol";

interface IBurnableToken {
    function burn(address from, uint256 amount) external;
}

/**
 * @title RioOTOFGovernor - Governança Quadrática para OTOF
 * @notice Prevenção de dominação por whales via custo quadrático de voto
 */
contract RioOTOFGovernor is Governor, GovernorSettings, GovernorVotes, GovernorCountingSimple, GovernorTimelockControl {

    // Parâmetros EQBE
    uint256 public constant QUORUM_PERCENT = 4; // 4% do supply

    // Estrutura de proposta médica
    struct MedicalProposal {
        bytes32 geneticHash;        // Paciente alvo (anonimizado)
        uint256 requestedAmount;    // Valor solicitado
        string justificationURI;    // IPFS link (laudos, exames)
        uint256 forVotes;
        uint256 againstVotes;
        mapping(address => uint256) voiceCreditsSpent; // Rastreamento
        bool executed;
        uint256 lambdaRequirement;  // Coerência mínima requerida
    }

    mapping(uint256 => MedicalProposal) public medicalProposals;
    uint256 public medicalProposalCount;

    event VoteCastQuadratic(
        uint256 indexed proposalId,
        address voter,
        bool support,
        uint256 votes, // Número de votos (peso)
        uint256 cost    // Custo em RIO (quadrático)
    );

    constructor(IVotes _token, TimelockController _timelock)
        Governor("RioOTOFGovernor")
        GovernorSettings(1, 50400, 1000e18) // 1 block delay, ~1 week period, 1000 RIO threshold
        GovernorVotes(_token)
        GovernorTimelockControl(_timelock)
    {}

    /**
     * @notice Votação quadrática: custo = votos²
     * Exemplo: 1 voto = 1 RIO, 2 votos = 4 RIO, 10 votos = 100 RIO
     */
    function castVoteQuadratic(
        uint256 proposalId,
        uint8 support,
        uint256 voiceCredits
    ) external returns (uint256) {
        require(state(proposalId) == ProposalState.Active, "VOTING_NOT_ACTIVE");

        // Cálculo quadrático: custo = (votos)²
        uint256 cost = voiceCredits * voiceCredits;
        require(
            getVotes(msg.sender, proposalSnapshot(proposalId)) >= cost,
            "INSUFFICIENT_BALANCE"
        );

        // Queima tokens (requer que o token implemente burn ou que este contrato tenha permissão)
        IBurnableToken(address(token())).burn(msg.sender, cost);

        // Update Governor state
        _countVote(proposalId, msg.sender, support, voiceCredits, "");

        MedicalProposal storage p = medicalProposals[0];
        // Registra gasto para auditoria
        p.voiceCreditsSpent[msg.sender] += voiceCredits;

        if (support == 1) {
            p.forVotes += voiceCredits;
        } else if (support == 0) {
            p.againstVotes += voiceCredits;
        }

        emit VoteCastQuadratic(proposalId, msg.sender, support == 1, voiceCredits, cost);
        return voiceCredits;
    }

    /**
     * @notice Cria proposta de subsídio médico
     */
    function proposeMedicalSubsidy(
        bytes32 geneticHash,
        uint256 amount,
        string calldata justificationURI,
        uint256 lambdaMin
    ) external returns (uint256) {
        require(
            getVotes(msg.sender, block.number - 1) >= proposalThreshold(),
            "BELOW_PROPOSAL_THRESHOLD"
        );

        uint256 id = medicalProposalCount++;
        MedicalProposal storage p = medicalProposals[id];
        p.geneticHash = geneticHash;
        p.requestedAmount = amount;
        p.justificationURI = justificationURI;
        p.lambdaRequirement = lambdaMin;

        // Agendamento automático
        address[] memory targets = new address[](1);
        targets[0] = address(this);
        uint256[] memory values = new uint256[](1);
        values[0] = 0;
        bytes[] memory calldatas = new bytes[](1);
        calldatas[0] = "";

        return propose(
            targets,
            values,
            calldatas,
            string(abi.encodePacked("OTOF_Subsidy_", _uint2str(id)))
        );
    }

    function _uint2str(uint256 _i) internal pure returns (string memory _uintAsString) {
        if (_i == 0) {
            return "0";
        }
        uint256 j = _i;
        uint256 len;
        while (j != 0) {
            len++;
            j /= 10;
        }
        bytes memory bstr = new bytes(len);
        uint256 k = len;
        while (_i != 0) {
            k = k - 1;
            uint8 temp = (48 + uint8(_i - (_i / 10) * 10));
            bytes1 b1 = bytes1(temp);
            bstr[k] = b1;
            _i /= 10;
        }
        return string(bstr);
    }

    // Overrides necessários...
    function votingDelay() public view override(Governor, GovernorSettings) returns (uint256) { return super.votingDelay(); }
    function votingPeriod() public view override(Governor, GovernorSettings) returns (uint256) { return super.votingPeriod(); }
    function quorum(uint256 blockNumber) public view override(Governor) returns (uint256) {
        return (token().getPastTotalSupply(blockNumber) * QUORUM_PERCENT) / 100;
    }
    function state(uint256 proposalId) public view override(Governor, GovernorTimelockControl) returns (ProposalState) { return super.state(proposalId); }
    function proposalThreshold() public view override(Governor, GovernorSettings) returns (uint256) { return super.proposalThreshold(); }
    function _executeOperations(uint256 proposalId, address[] memory targets, uint256[] memory values, bytes[] memory calldatas, bytes32 descriptionHash) internal override(Governor, GovernorTimelockControl) { super._executeOperations(proposalId, targets, values, calldatas, descriptionHash); }
    function _cancel(address[] memory targets, uint256[] memory values, bytes[] memory calldatas, bytes32 descriptionHash) internal override(Governor, GovernorTimelockControl) returns (uint256) { return super._cancel(targets, values, calldatas, descriptionHash); }
    function _executor() internal view override(Governor, GovernorTimelockControl) returns (address) { return super._executor(); }
    function proposalNeedsQueuing(uint256 proposalId) public view override(Governor, GovernorTimelockControl) returns (bool) { return super.proposalNeedsQueuing(proposalId); }
    function _queueOperations(uint256 proposalId, address[] memory targets, uint256[] memory values, bytes[] memory calldatas, bytes32 descriptionHash) internal override(Governor, GovernorTimelockControl) returns (uint48) { return super._queueOperations(proposalId, targets, values, calldatas, descriptionHash); }
}
