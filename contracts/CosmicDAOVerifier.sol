// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "./interfaces/IGroth16Verifier.sol";

/**
 * @title CosmicDAOVerifier
 * @dev Contrato para registro imutável de provas de coerência neural
 *
 * Funcionalidades:
 * - Verificação de provas Groth16 on-chain
 * - Registro de métricas Ω com timestamp e autor
 * - Sistema de reputação baseado em provas válidas
 * - Eventos para indexação off-chain (The Graph)
 * - Gas optimization para transações frequentes
 */
contract CosmicDAOVerifier is Ownable, ReentrancyGuard {

    // Estrutura para registro de prova
    struct CoherenceProof {
        uint256 proofId;
        address prover;
        uint256 omegaScaled;      // Ω * 1e6 para precisão inteira
        uint256 timestamp;
        bytes32 signalHash;       // Hash do sinal original (para binding)
        bytes32 metadataHash;     // Hash de metadados do experimento
        bool isValid;
        uint256 gasUsed;
    }

    // Estrutura para reputação de prover
    struct ProverReputation {
        uint256 validProofs;
        uint256 totalProofs;
        uint256 lastProofTimestamp;
        uint256 reputationScore;  // Calculado: validProofs / totalProofs * time_decay
    }

    // Mapeamentos principais
    mapping(bytes32 => CoherenceProof) public proofs;  // signalHash → proof
    mapping(address => ProverReputation) public reputations;
    mapping(uint256 => bytes32) public proofIndex;     // proofId → signalHash

    // Contadores e configurações
    uint256 public nextProofId;
    uint256 public totalValidProofs;
    uint256 public constant OMEGA_PRECISION = 1e6;  // Precisão para Ω
    uint256 public constant MIN_OMEGA_THRESHOLD = 700000;  // 0.7 * 1e6

    // Verificador Groth16 externo (deployed separadamente)
    IGroth16Verifier public groth16Verifier;

    // Eventos para indexação
    event ProofSubmitted(
        uint256 indexed proofId,
        address indexed prover,
        uint256 omegaScaled,
        bytes32 indexed signalHash,
        bool isValid,
        uint256 timestamp
    );

    event ReputationUpdated(
        address indexed prover,
        uint256 validProofs,
        uint256 totalProofs,
        uint256 reputationScore
    );

    event VerifierUpdated(
        address indexed oldVerifier,
        address indexed newVerifier
    );

    constructor(address _groth16Verifier) {
        groth16Verifier = IGroth16Verifier(_groth16Verifier);
        nextProofId = 1;
    }

    /**
     * @dev Submete prova de coerência para verificação e registro
     * @param _omegaScaled Valor de Ω escalado por 1e6 (para precisão)
     * @param _signalHash Hash do sinal neural original
     * @param _metadataHash Hash de metadados do experimento
     * @param _proof Dados da prova Groth16 {pi_a, pi_b, pi_c, public_signals}
     * @return proofId ID único do registro
     */
    function submitCoherenceProof(
        uint256 _omegaScaled,
        bytes32 _signalHash,
        bytes32 _metadataHash,
        IGroth16Verifier.Groth16Proof calldata _proof
    ) external nonReentrant returns (uint256) {
        require(_omegaScaled <= OMEGA_PRECISION, "Omega out of range");
        require(proofs[_signalHash].proofId == 0, "Proof already submitted");

        // Verificar prova criptográfica (on-chain)
        bool proofValid = groth16Verifier.verifyProof(
            _proof.pi_a,
            _proof.pi_b,
            _proof.pi_c,
            _proof.public_signals  // [omega_scaled, threshold, salt]
        );

        // Verificar consistência: Ω deve estar acima do threshold se prova válida
        if (proofValid) {
            require(_omegaScaled >= MIN_OMEGA_THRESHOLD, "Omega below threshold");
        }

        // Criar registro
        uint256 proofId = nextProofId++;
        CoherenceProof storage newProof = proofs[_signalHash];
        newProof.proofId = proofId;
        newProof.prover = msg.sender;
        newProof.omegaScaled = _omegaScaled;
        newProof.timestamp = block.timestamp;
        newProof.signalHash = _signalHash;
        newProof.metadataHash = _metadataHash;
        newProof.isValid = proofValid;
        newProof.gasUsed = gasleft();  // Estimativa de gas usado

        // Atualizar índice
        proofIndex[proofId] = _signalHash;

        // Atualizar reputação do prover
        _updateReputation(msg.sender, proofValid);

        // Atualizar contadores globais
        if (proofValid) {
            totalValidProofs++;
        }

        // Emitir evento para indexação off-chain
        emit ProofSubmitted(
            proofId,
            msg.sender,
            _omegaScaled,
            _signalHash,
            proofValid,
            block.timestamp
        );

        return proofId;
    }

    /**
     * @dev Atualiza reputação de um prover baseado em histórico de provas
     */
    function _updateReputation(address _prover, bool _proofValid) internal {
        ProverReputation storage rep = reputations[_prover];

        rep.totalProofs++;
        if (_proofValid) {
            rep.validProofs++;
        }
        rep.lastProofTimestamp = block.timestamp;

        // Calcular score de reputação com decaimento temporal
        // Fórmula: (valid/total) * (1 / (1 + days_since_first_proof / 30))
        uint256 timeSinceLast = block.timestamp - rep.lastProofTimestamp;
        uint256 timeFactor = 1e18 / (1 + timeSinceLast / 30 days);
        rep.reputationScore = (rep.validProofs * 1e18 / rep.totalProofs) * timeFactor / 1e18;

        emit ReputationUpdated(
            _prover,
            rep.validProofs,
            rep.totalProofs,
            rep.reputationScore
        );
    }

    /**
     * @dev Consulta prova por signalHash
     */
    function getProof(bytes32 _signalHash) external view returns (CoherenceProof memory) {
        return proofs[_signalHash];
    }

    /**
     * @dev Consulta reputação de um prover
     */
    function getReputation(address _prover) external view returns (ProverReputation memory) {
        return reputations[_prover];
    }

    /**
     * @dev Atualiza endereço do verificador Groth16 (apenas owner)
     */
    function updateGroth16Verifier(address _newVerifier) external onlyOwner {
        emit VerifierUpdated(address(groth16Verifier), _newVerifier);
        groth16Verifier = IGroth16Verifier(_newVerifier);
    }

    /**
     * @dev Função para batch submission (gas optimization)
     */
    function batchSubmitProofs(
        uint256[] calldata _omegaScaleds,
        bytes32[] calldata _signalHashes,
        bytes32[] calldata _metadataHashes,
        IGroth16Verifier.Groth16Proof[] calldata _proofs
    ) external nonReentrant returns (uint256[] memory) {
        require(
            _omegaScaleds.length == _signalHashes.length &&
            _signalHashes.length == _metadataHashes.length &&
            _metadataHashes.length == _proofs.length,
            "Array length mismatch"
        );

        uint256[] memory proofIds = new uint256[](_proofs.length);

        for (uint256 i = 0; i < _proofs.length; i++) {
            proofIds[i] = submitCoherenceProof(
                _omegaScaleds[i],
                _signalHashes[i],
                _metadataHashes[i],
                _proofs[i]
            );
        }

        return proofIds;
    }
}
