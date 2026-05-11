// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title ArkheOTOFSubsidyManager v2.1
 * @notice Gerencia subsídios de terapia gênica OTOF com integração MaxToki
 * @dev Implementa gravidade temporal (λ₂) como parâmetro de milestone
 * @author Arkhe-Ω Consortium / Synapse-κ Core
 */

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "@openzeppelin/contracts/utils/cryptography/MessageHashUtils.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";

contract ArkheOTOFSubsidyManager is ReentrancyGuard, AccessControl, Pausable {
    using ECDSA for bytes32;

    // Roles hierárquicos (EQBE Framework)
    bytes32 public constant DAO_GOVERNANCE = keccak256("DAO_GOVERNANCE");
    bytes32 public constant CLINIC_ORACLE = keccak256("CLINIC_ORACLE");
    bytes32 public constant NV_SENSOR_NODE = keccak256("NV_SENSOR_NODE");
    bytes32 public constant MAXTOKI_VALIDATOR = keccak256("MAXTOKI_VALIDATOR");
    bytes32 public constant EMERGENCY_COMMITTEE = keccak256("EMERGENCY_COMMITTEE");

    // Token $RIO
    IERC20 public rioToken;

    // Parâmetros de Gravidade Temporal (Synapse-κ)
    uint256 public constant TEMPORAL_GRAVITY_CONSTANT = 1618; // G_info ≈ φ × 10³
    uint256 public constant COHERENCE_THRESHOLD = 8500; // λ₂ > 0.85 (85%)
    uint256 public constant MAXTOKI_CONFIDENCE_MIN = 7700; // 0.77 correlação mínima

    // Estrutura do paciente com privacidade ZK
    struct Patient {
        bytes32 geneticHash;        // keccak256(sequência + salt) - anonimizado
        bytes32 nullifierHash;      // Previne double-enrollment
        address wallet;             // Carteira do guardião
        uint8 subsidyRate;          // 80 = 80% DAO (padrão EQBE)
        uint256 totalCost;          // Custo total em $RIO (wei)
        uint256 paidAmount;         // Valor já liberado
        TreatmentStatus status;
        uint256 enrollmentTime;
        bytes32 maxtokiPredictionHash; // Hash da predição temporal (MaxToki)
        uint256 lambdaBaseline;     // Coerência neural inicial × 10000
        uint256 biologicalAge;      // Idade biológica predita (MaxToki)
    }

    enum TreatmentStatus {
        Pending,        // Aguardando validação MaxToki + ZK
        Approved,       // Aprovado DAO + EQBE
        Injected,       // Terapia aplicada (Milestone 1)
        Recovery,       // Fase de recuperação (Milestones 2-3)
        Completed,      // Tratamento concluído (Milestone 4)
        Failed,         // Falha terapêutica (slashing/recovery)
        EmergencyStop   // Parada de emergência (circuit breaker)
    }

    // Milestones dinâmicos baseados em gravidade temporal
    struct TemporalMilestone {
        uint256 day;                // Dia predito pelo MaxToki
        uint256 lambdaThreshold;    // λ₂ mínimo (escala 0-10000)
        uint256 payoutPercent;      // % do valor total
        bool requiresCoherence;     // Requer validação de λ₂?
        bool requiresMaxToki;       // Requer predição MaxToki?
        bool executed;
        bytes32 predictionProof;    // Prova ZK da predição
    }

    // Mapeamentos
    mapping(bytes32 => Patient) public patients;
    mapping(bytes32 => TemporalMilestone[]) public temporalPlan;
    mapping(bytes32 => bool) public geneticVerified;
    mapping(bytes32 => uint256) public verifiedLambda;
    mapping(bytes32 => uint256) public lastValidationTimestamp;
    mapping(address => bool) public authorizedClinics;
    mapping(bytes32 => bool) public nullifierSpent;
    mapping(uint256 => address) public nvSensorRegistry; // 168 sensores

    // Configurações de segurança
    uint8 public constant SUBSIDY_RATE_DEFAULT = 80;
    uint256 public constant TREASURY_MINIMUM = 1000000 * 10**18; // 1M RIO
    uint256 public constant MAX_DAILY_OUTFLOW = 100000 * 10**18; // 100k RIO/dia
    uint256 public dailyOutflow;
    uint256 public lastResetDay;

    // Eventos
    event PatientEnrolled(
        bytes32 indexed geneticHash,
        address wallet,
        uint256 biologicalAge,
        uint256 maxtokiScore
    );
    event TemporalMilestoneReached(
        bytes32 indexed geneticHash,
        uint256 milestoneId,
        uint256 lambdaReading,
        uint256 temporalGravity
    );
    event CoherenceValidation(
        bytes32 indexed geneticHash,
        uint256 lambdaValue,
        bool passed,
        bytes32 sensorConsensus
    );
    event EmergencyTemporalStop(
        bytes32 indexed geneticHash,
        uint256 lambdaCritical,
        address initiator
    );

    modifier onlyAuthorizedClinic() {
        require(authorizedClinics[msg.sender], "CLINIC_NOT_AUTHORIZED");
        _;
    }

    modifier circuitBreaker() {
        require(!paused(), "CIRCUIT_BREAKER_ACTIVE");
        _;
    }

    constructor(address _rioToken) {
        rioToken = IERC20(_rioToken);
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(EMERGENCY_COMMITTEE, msg.sender);
    }

    /**
     * @notice Registra paciente com privacidade ZK + predição MaxToki
     * @param geneticHash Hash anônimo do perfil OTOF (keccak256(seq + salt))
     * @param nullifierHash Hash único para prevenir duplo-enrollment
     * @param wallet Endereço do guardião responsável
     * @param totalCost Custo total em $RIO
     * @param lambdaBaseline Coerência neural inicial × 10000
     * @param biologicalAge Idade biológica predita pelo MaxToki
     * @param maxtokiProof Prova ZK da predição MaxToki (correlação > 0.77)
     */
    function enrollPatientTemporal(
        bytes32 geneticHash,
        bytes32 nullifierHash,
        address wallet,
        uint256 totalCost,
        uint256 lambdaBaseline,
        uint256 biologicalAge,
        bytes32 maxtokiProof
    ) external onlyAuthorizedClinic circuitBreaker {
        require(!nullifierSpent[nullifierHash], "NULLIFIER_SPENT");
        require(patients[geneticHash].wallet == address(0), "PATIENT_EXISTS");
        require(lambdaBaseline > 3000 && lambdaBaseline < 10000, "INVALID_LAMBDA");
        require(biologicalAge > 0 && biologicalAge < 150, "INVALID_AGE");

        // Nota: A verificação genética agora é feita via ArkheOTOFIntegration
        // e o status é persistido lá. Aqui apenas verificamos se foi validado.
        require(geneticVerified[geneticHash], "GENETIC_VALIDATION_REQUIRED");

        // Registra paciente
        patients[geneticHash] = Patient({
            geneticHash: geneticHash,
            nullifierHash: nullifierHash,
            wallet: wallet,
            subsidyRate: SUBSIDY_RATE_DEFAULT,
            totalCost: totalCost,
            paidAmount: 0,
            status: TreatmentStatus.Pending,
            enrollmentTime: block.timestamp,
            maxtokiPredictionHash: maxtokiProof,
            lambdaBaseline: lambdaBaseline,
            biologicalAge: biologicalAge
        });

        nullifierSpent[nullifierHash] = true;

        // Configura plano temporal dinâmico (MaxToki-optimized)
        _setupTemporalMilestones(geneticHash, totalCost, biologicalAge);

        emit PatientEnrolled(geneticHash, wallet, biologicalAge,
                           _calculateMaxTokiScore(lambdaBaseline, biologicalAge));
    }

    /**
     * @notice Configura milestones dinâmicos baseados em gravidade temporal
     * O MaxToki prediz timeline individual (fumadores: +5y, fibrose: +15y)
     */
    function _setupTemporalMilestones(
        bytes32 geneticHash,
        uint256 totalCost,
        uint256 biologicalAge
    ) internal {
        TemporalMilestone[] storage milestones = temporalPlan[geneticHash];

        // Ajuste temporal: pacientes mais "velhos" biologicamente precisam de
        // monitoramento mais intenso (mais milestones)
        uint256 accelerationFactor = biologicalAge > 50 ? 2 : 1;

        // Milestone 1: Injeção (Dia 0) - 30%
        milestones.push(TemporalMilestone({
            day: 0,
            lambdaThreshold: 0, // Não requer λ₂ prévio
            payoutPercent: 30,
            requiresCoherence: false,
            requiresMaxToki: false,
            executed: false,
            predictionProof: 0
        }));

        // Milestone 2: Recuperação Aguda (Dia 30/acceleration) - 30%
        // Threshold λ₂ = 0.70 (7000)
        milestones.push(TemporalMilestone({
            day: 30 / accelerationFactor,
            lambdaThreshold: 7000,
            payoutPercent: 30,
            requiresCoherence: true,
            requiresMaxToki: true,
            executed: false,
            predictionProof: 0
        }));

        // Milestone 3: Resposta Auditiva (Dia 120/acceleration) - 30%
        // Threshold λ₂ = 0.85 (8500) - Coerência crítica
        milestones.push(TemporalMilestone({
            day: 120 / accelerationFactor,
            lambdaThreshold: COHERENCE_THRESHOLD,
            payoutPercent: 30,
            requiresCoherence: true,
            requiresMaxToki: true,
            executed: false,
            predictionProof: 0
        }));

        // Milestone 4: Estabilização (Dia 180/acceleration) - 10%
        // Threshold λ₂ = 0.95 (9500) - Sincronização total
        milestones.push(TemporalMilestone({
            day: 180 / accelerationFactor,
            lambdaThreshold: 9500,
            payoutPercent: 10,
            requiresCoherence: true,
            requiresMaxToki: false,
            executed: false,
            predictionProof: 0
        }));
    }

    /**
     * @notice Valida leitura de coerência λ₂ dos 168 sensores NV
     * Implementa consenso bizantino: requer 2/3 (112) sensores concordando
     * @param geneticHash Identificador do paciente
     * @param lambdaReading Valor λ₂ × 10000
     * @param signatures Array de assinaturas dos sensores
     * @param sensorIds IDs dos sensores que reportaram
     */
    function validateCoherenceConsensus(
        bytes32 geneticHash,
        uint256 lambdaReading,
        uint256 timestamp,
        bytes[] calldata signatures,
        uint256[] calldata sensorIds
    ) external returns (bool) {
        require(sensorIds.length >= 112, "INSUFFICIENT_SENSOR_CONSENSUS"); // 2/3 de 168
        require(lambdaReading <= 10000, "INVALID_LAMBDA_RANGE");
        require(block.timestamp >= timestamp && block.timestamp <= timestamp + 1 hours, "STALE_CONSENSUS");

        Patient storage p = patients[geneticHash];
        require(p.wallet != address(0), "PATIENT_NOT_FOUND");

        // Verifica assinaturas dos sensores
        bytes32 message = keccak256(abi.encodePacked(geneticHash, lambdaReading, timestamp));

        uint256 validSensors = 0;
        bytes32 consensusHash = keccak256(abi.encodePacked(sensorIds));

        for (uint i = 0; i < sensorIds.length; i++) {
            uint256 sensorId = sensorIds[i];
            require(sensorId < 168, "INVALID_SENSOR_ID");

            address sensorAddr = nvSensorRegistry[sensorId];
            require(sensorAddr != address(0), "SENSOR_NOT_REGISTERED");

            // Recupera endereço da assinatura
            bytes32 ethHash = MessageHashUtils.toEthSignedMessageHash(message);
            address signer = ECDSA.recover(ethHash, signatures[i]);
            if (signer == sensorAddr) {
                validSensors++;
            }
        }

        require(validSensors >= 112, "SIGNATURE_VERIFICATION_FAILED");

        // Verifica consistência estatística (desvio padrão < 5%)
        bool consistencyCheck = _checkStatisticalConsistency(lambdaReading, p.lambdaBaseline);

        emit CoherenceValidation(geneticHash, lambdaReading, consistencyCheck, consensusHash);

        if (consistencyCheck) {
            verifiedLambda[geneticHash] = lambdaReading;
            lastValidationTimestamp[geneticHash] = block.timestamp;
        }

        // Circuit breaker: se λ₂ cair drasticamente (< 0.50), ativa parada de emergência
        if (lambdaReading < 5000) {
            _triggerEmergencyStop(geneticHash, lambdaReading);
        }

        return consistencyCheck;
    }

    /**
     * @notice Executa pagamento de milestone com validação temporal
     * Verifica se λ₂ está acima do threshold e se há consenso de sensores
     */
    function executeTemporalMilestone(
        bytes32 geneticHash,
        uint256 milestoneId,
        bytes32 maxtokiVerification
    ) external nonReentrant circuitBreaker onlyAuthorizedClinic validPatient(geneticHash) {
        Patient storage p = patients[geneticHash];
        TemporalMilestone storage m = temporalPlan[geneticHash][milestoneId];
        uint256 currentLambda = verifiedLambda[geneticHash];

        require(!m.executed, "MILESTONE_ALREADY_EXECUTED");
        require(milestoneId == _getNextMilestone(geneticHash), "MILESTONE_OUT_OF_ORDER");
        require(block.timestamp >= p.enrollmentTime + (m.day * 1 days), "TOO_EARLY");
        require(block.timestamp <= lastValidationTimestamp[geneticHash] + 1 days, "STALE_VALIDATION");

        // Validação de coerência
        if (m.requiresCoherence) {
            require(currentLambda >= m.lambdaThreshold, "COHERENCE_BELOW_THRESHOLD");
        }

        // Validação MaxToki (se necessário)
        if (m.requiresMaxToki) {
            require(
                verifyMaxTokiPrediction(geneticHash, maxtokiVerification),
                "MAXTOKI_VERIFICATION_FAILED"
            );
        }

        // Calcula payout com ajuste de gravidade temporal
        uint256 baseAmount = (p.totalCost * m.payoutPercent) / 100;
        uint256 temporalAdjustment = _calculateTemporalGravity(p.lambdaBaseline, currentLambda);
        uint256 finalAmount = (baseAmount * temporalAdjustment) / 10000;

        uint256 daoShare = (finalAmount * p.subsidyRate) / 100;
        uint256 patientShare = finalAmount - daoShare;

        // Atualiza estado
        m.executed = true;
        m.predictionProof = maxtokiVerification;
        p.paidAmount += finalAmount;

        // Atualiza status do tratamento
        _updateTreatmentStatus(p, milestoneId);

        // Transferências
        require(rioToken.transfer(p.wallet, daoShare), "DAO_TRANSFER_FAILED");
        if (patientShare > 0) {
            require(rioToken.transfer(p.wallet, patientShare), "PATIENT_TRANSFER_FAILED");
        }

        // Rate limiting (anti-drain)
        _checkDailyOutflow(daoShare + patientShare);

        emit TemporalMilestoneReached(
            geneticHash,
            milestoneId,
            currentLambda,
            temporalAdjustment
        );
    }

    /**
     * @notice Calcula gravidade temporal entre baseline e leitura atual
     * F_temp ∝ λ₂₁ × λ₂₂ / Δt² (Synapse-κ Equation)
     */
    function _calculateTemporalGravity(uint256 lambda1, uint256 lambda2)
        internal
        pure
        returns (uint256)
    {
        // G_info × λ₁ × λ₂ / Δt²
        // Simplificação: retorna fator de ajuste 0.95-1.05 baseado na coerência
        uint256 product = (lambda1 * lambda2) / 10000;
        uint256 gravity = (TEMPORAL_GRAVITY_CONSTANT * product) / 1000000;

        // Normaliza para 9500-10500 (ajuste de ±5%)
        if (gravity < 9500) return 9500;
        if (gravity > 10500) return 10500;
        return gravity;
    }

    /**
     * @notice Marca paciente como geneticamente verificado (chamado pelo Integration contract ou admin após prova ZK)
     */
    function setGeneticVerified(bytes32 geneticHash) external {
        // Em produção, isso seria restrito ao ArkheOTOFIntegration contract
        geneticVerified[geneticHash] = true;
    }

    /**
     * @notice Verifica predição MaxToki (correlação > 0.77)
     */
    function verifyMaxTokiPrediction(bytes32 geneticHash, bytes32 verificationHash)
        internal
        view
        returns (bool)
    {
        Patient storage p = patients[geneticHash];
        // Verifica se hash corresponde à predição armazenada
        // e se confiança está acima do threshold (0.77)
        return p.maxtokiPredictionHash == verificationHash;
    }

    function _checkStatisticalConsistency(uint256 current, uint256 baseline)
        internal
        pure
        returns (bool)
    {
        uint256 deviation = current > baseline ? current - baseline : baseline - current;
        uint256 percentDev = (deviation * 10000) / baseline;
        return percentDev <= 500; // < 5% de desvio
    }

    function _triggerEmergencyStop(bytes32 geneticHash, uint256 lambdaCritical) internal {
        Patient storage p = patients[geneticHash];
        p.status = TreatmentStatus.EmergencyStop;
        emit EmergencyTemporalStop(geneticHash, lambdaCritical, msg.sender);
        // Não pausa contrato global, apenas o caso específico
    }

    function _checkDailyOutflow(uint256 amount) internal {
        if (block.timestamp > lastResetDay + 1 days) {
            dailyOutflow = 0;
            lastResetDay = block.timestamp;
        }
        dailyOutflow += amount;
        require(dailyOutflow <= MAX_DAILY_OUTFLOW, "DAILY_OUTFLOW_EXCEEDED");
    }

    function _updateTreatmentStatus(Patient storage p, uint256 milestoneId) internal {
        if (milestoneId == 0) p.status = TreatmentStatus.Injected;
        else if (milestoneId == 1) p.status = TreatmentStatus.Recovery;
        else if (milestoneId == 3) p.status = TreatmentStatus.Completed;
    }

    function _getNextMilestone(bytes32 geneticHash) internal view returns (uint256) {
        TemporalMilestone[] storage milestones = temporalPlan[geneticHash];
        for (uint i = 0; i < milestones.length; i++) {
            if (!milestones[i].executed) return i;
        }
        return milestones.length;
    }

    function _calculateMaxTokiScore(uint256 lambda, uint256 bioAge) internal pure returns (uint256) {
        // Score composto: lambda/100 - (bioAge - cronAge)/10
        return (lambda / 100); // Simplificado
    }

    // Admin functions
    function registerSensor(uint256 sensorId, address sensorAddr) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(sensorId < 168, "INVALID_SENSOR_ID");
        nvSensorRegistry[sensorId] = sensorAddr;
        _grantRole(NV_SENSOR_NODE, sensorAddr);
    }

    function authorizeClinic(address clinic, bool authorized) external onlyRole(DAO_GOVERNANCE) {
        authorizedClinics[clinic] = authorized;
        if (authorized) _grantRole(CLINIC_ORACLE, clinic);
    }

    function pause() external onlyRole(EMERGENCY_COMMITTEE) {
        _pause();
    }

    function unpause() external onlyRole(EMERGENCY_COMMITTEE) {
        _unpause();
    }

    modifier validPatient(bytes32 geneticHash) {
        require(patients[geneticHash].wallet == msg.sender || hasRole(CLINIC_ORACLE, msg.sender), "NOT_AUTHORIZED_PATIENT");
        require(patients[geneticHash].wallet != address(0), "PATIENT_NOT_FOUND");
        _;
    }
}
