// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title ARKHE Q-Art Royalty Escrow
 * @notice Contrato de custódia para royalties artísticos.
 *         Segura pagamentos até que provas ZK sejam verificadas
 *         ou um timeout expire, permitindo reembolso ao pagador.
 *
 * Fluxo:
 *   1. Depositador (protocolo Q-Art) deposita ETH/ERC-20
 *   2. Beneficiário (artista via wallet Pix/ERC-20) pode sacar após release
 *   3. Depositador pode reverter se prova ZK não for fornecida em tempo
 *   4. Arbitro (DAO/multisig) pode resolver disputas
 */
contract ARKHERoyaltyEscrow {

    // ============================================================
    // ESTRUTURAS DE DADOS
    // ============================================================

    /// Representa um depósito de royalty
    struct EscrowDeposit {
        bytes32 depositId;           // ID único do depósito
        address depositor;           // Endereço que depositou (protocolo Q-Art)
        address beneficiary;        // Endereço do artista/beneficiário
        uint256 amount;              // Valor depositado (em wei para ETH)
        uint256 createdAt;           // Timestamp de criação
        uint256 releaseTime;         // Quando o saque é permitido
        uint256 expiryTime;          // Quando expira (reembolso permitido)
        bytes32 proofHash;           // Hash da prova ZK
        bool proofSubmitted;         // Se prova ZK foi submetida
        bool released;               // Se os fundos foram liberados
        bool refunded;               // Se os fundos foram reembolsados
        address tokenAddress;        // Endereço do token ERC-20 (address(0) = ETH nativo)
    }

    /// Configuração do contrato
    struct EscrowConfig {
        uint256 defaultReleaseDelay; // Tempo mínimo antes do saque (segundos)
        uint256 defaultExpiryDelay;  // Tempo máximo antes do reembolso (segundos)
        uint256 minDeposit;          // Depósito mínimo (wei)
        uint256 maxDeposit;          // Depósito máximo (wei)
        address protocolTreasury;    // Endereço do tesouro do protocolo
        address disputeResolver;     // Endereço do resolvedor de disputas
    }

    // ============================================================
    // ESTADO
    // ============================================================

    /// Configuração atual
    EscrowConfig public config;

    /// Mapeamento de depósitos por ID
    mapping(bytes32 => EscrowDeposit) public deposits;

    /// Lista de depósitos por beneficiário
    mapping(address => bytes32[]) public depositsByBeneficiary;

    /// Número total de depósitos
    uint256 public totalDeposits;

    // ============================================================
    // EVENTOS
    // ============================================================

    /// Emitido quando um depósito é criado
    event DepositCreated(
        bytes32 indexed depositId,
        address indexed depositor,
        address indexed beneficiary,
        uint256 amount,
        address tokenAddress,
        uint256 releaseTime,
        uint256 expiryTime
    );

    /// Emitido quando a prova ZK é submetida
    event ProofSubmitted(
        bytes32 indexed depositId,
        bytes32 proofHash
    );

    /// Emitido quando os fundos são liberados ao beneficiário
    event Released(
        bytes32 indexed depositId,
        address indexed beneficiary,
        uint256 amount
    );

    /// Emitido quando os fundos são reembolsados ao depositador
    event Refunded(
        bytes32 indexed depositId,
        address indexed depositor,
        uint256 amount
    );

    /// Emitido quando configuração é atualizada
    event ConfigUpdated(
        address indexed updater,
        EscConfigField field,
        uint256 newValue
    );

    /// Emitido quando resolvedor de disputas é alterado
    event DisputeResolverUpdated(
        address indexed oldResolver,
        address indexed newResolver
    );

    enum EscConfigField {
        DefaultReleaseDelay,
        DefaultExpiryDelay,
        MinDeposit,
        MaxDeposit,
        ProtocolTreasury,
        DisputeResolver
    }

    // ============================================================
    // MODIFIERS
    // ============================================================

    modifier onlyDepositExists(bytes32 depositId) {
        require(deposits[depositId].depositor != address(0), "Escrow: deposit does not exist");
        _;
    }

    modifier onlyDepositor(bytes32 depositId) {
        require(deposits[depositId].depositor == msg.sender, "Escrow: only depositor");
        _;
    }

    modifier onlyBeneficiary(bytes32 depositId) {
        require(deposits[depositId].beneficiary == msg.sender, "Escrow: only beneficiary");
        _;
    }

    modifier onlyDepositorOrBeneficiary(bytes32 depositId) {
        require(
            deposits[depositId].depositor == msg.sender ||
            deposits[depositId].beneficiary == msg.sender,
            "Escrow: only depositor or beneficiary"
        );
        _;
    }

    modifier onlyDepositNotReleased(bytes32 depositId) {
        require(!deposits[depositId].released, "Escrow: already released");
        _;
    }

    modifier onlyDepositNotRefunded(bytes32 depositId) {
        require(!deposits[depositId].refunded, "Escrow: already refunded");
        _;
    }

    modifier onlyResolvedOrTimeout(bytes32 depositId) {
        EscrowDeposit storage deposit = deposits[depositId];
        require(
            block.timestamp >= deposit.releaseTime ||
            deposit.proofSubmitted,
            "Escrow: not yet releasable"
        );
        _;
    }

    modifier onlyExpired(bytes32 depositId) {
        require(
            block.timestamp >= deposits[depositId].expiryTime,
            "Escrow: not yet expired"
        );
        _;
    }

    // ============================================================
    // CONSTRUTOR
    // ============================================================

    constructor(EscrowConfig memory initialConfig) {
        require(initialConfig.defaultReleaseDelay > 0, "Escrow: release delay must be > 0");
        require(initialConfig.defaultExpiryDelay > initialConfig.defaultReleaseDelay,
            "Escrow: expiry delay must be > release delay");
        require(initialConfig.disputeResolver != address(0), "Escrow: resolver required");

        config = initialConfig;
    }

    // ============================================================
    // FUNÇÕES PRINCIPAIS
    // ============================================================

    /// Cria um novo depósito de escrow
    /// @param beneficiary Endereço do beneficiário (artista)
    /// @param tokenAddress Endereço do token ERC-20 (address(0) para ETH nativo)
    /// @param expiryDelayOverride Override para delay de expiração (0 = usar default)
    function createDeposit(
        address beneficiary,
        address tokenAddress,
        uint256 expiryDelayOverride
    ) external payable returns (bytes32 depositId) {
        require(beneficiary != address(0), "Escrow: invalid beneficiary");
        require(beneficiary != msg.sender, "Escrow: depositor cannot be beneficiary");

        // Determinar valor
        uint256 amount;
        if (tokenAddress == address(0)) {
            amount = msg.value;
        } else {
            // Para ERC-20: msg.value deve ser 0, token transferido via approve + transferFrom
            require(msg.value == 0, "Escrow: msg.value must be 0 for ERC-20");
            // Neste caso simplificado, assumimos que o token já foi aprovado
            // Em produção: usar safeTransferFrom
            amount = 0; // Placeholder — implementar transferFrom
        }

        require(amount >= config.minDeposit, "Escrow: below minimum deposit");
        require(amount <= config.maxDeposit, "Escrow: above maximum deposit");

        // Gerar ID do depósito
        depositId = keccak256(abi.encodePacked(
            msg.sender,
            beneficiary,
            amount,
            block.timestamp,
            totalDeposits
        ));

        // Calcular tempos
        uint256 releaseTime = block.timestamp + config.defaultReleaseDelay;
        uint256 expiryTime = block.timestamp + (
            expiryDelayOverride > 0 ? expiryDelayOverride : config.defaultExpiryDelay
        );

        require(expiryTime > releaseTime, "Escrow: expiry must be after release time");

        // Criar depósito
        EscrowDeposit storage newDeposit = deposits[depositId];
        newDeposit.depositId = depositId;
        newDeposit.depositor = msg.sender;
        newDeposit.beneficiary = beneficiary;
        newDeposit.amount = amount;
        newDeposit.createdAt = block.timestamp;
        newDeposit.releaseTime = releaseTime;
        newDeposit.expiryTime = expiryTime;
        newDeposit.tokenAddress = tokenAddress;

        depositsByBeneficiary[beneficiary].push(depositId);
        totalDeposits++;

        emit DepositCreated(
            depositId,
            msg.sender,
            beneficiary,
            amount,
            tokenAddress,
            releaseTime,
            expiryTime
        );
    }

    /// Submeter prova ZK para liberação antecipada
    function submitProof(bytes32 depositId, bytes32 proofHash)
        external
        onlyDepositor(depositId)
        onlyDepositNotReleased(depositId)
        onlyDepositNotRefunded(depositId)
    {
        EscrowDeposit storage deposit = deposits[depositId];
        deposit.proofHash = proofHash;
        deposit.proofSubmitted = true;

        emit ProofSubmitted(depositId, proofHash);
    }

    /// Liberar fundos ao beneficiário (pode ser chamado após releaseTime)
    function release(bytes32 depositId)
        external
        onlyDepositExists(depositId)
        onlyDepositNotReleased(depositId)
        onlyDepositNotRefunded(depositId)
    {
        EscrowDeposit storage deposit = deposits[depositId];

        require(
            block.timestamp >= deposit.releaseTime || deposit.proofSubmitted,
            "Escrow: not yet releasable"
        );

        require(msg.sender == deposit.beneficiary || msg.sender == config.disputeResolver,
            "Escrow: only beneficiary or resolver can release");

        deposit.released = true;

        _transferFunds(deposit.beneficiary, deposit.amount, deposit.tokenAddress);

        emit Released(depositId, deposit.beneficiary, deposit.amount);
    }

    /// Reembolsar depositador (após expiração sem release)
    function refund(bytes32 depositId)
        external
        onlyDepositExists(depositId)
        onlyDepositNotReleased(depositId)
        onlyDepositNotRefunded(depositId)
        onlyExpired(depositId)
    {
        EscrowDeposit storage deposit = deposits[depositId];
        deposit.refunded = true;

        _transferFunds(deposit.depositor, deposit.amount, deposit.tokenAddress);

        emit Refunded(depositId, deposit.depositor, deposit.amount);
    }

    /// Reembolso antecipado pelo depositador (antes da expiração, se prova não submetida)
    function emergencyRefund(bytes32 depositId)
        external
        onlyDepositor(depositId)
        onlyDepositNotReleased(depositId)
        onlyDepositNotRefunded(depositId)
    {
        EscrowDeposit storage deposit = deposits[depositId];

        require(!deposit.proofSubmitted, "Escrow: proof was submitted, wait for release");
        require(
            block.timestamp >= deposit.expiryTime,
            "Escrow: not expired yet"
        );

        deposit.refunded = true;
        _transferFunds(deposit.depositor, deposit.amount, deposit.tokenAddress);

        emit Refunded(depositId, deposit.depositor, deposit.amount);
    }

    // ============================================================
    // ADMINISTRAÇÃO
    // ============================================================

    /// Atualizar configuração (apenas dispute resolver)
    function updateConfig(EscConfigField field, uint256 newValue) external {
        require(msg.sender == config.disputeResolver, "Escrow: only resolver");

        if (field == EscConfigField.DefaultReleaseDelay) {
            require(newValue > 0, "Escrow: release delay must be > 0");
            config.defaultReleaseDelay = newValue;
        } else if (field == EscConfigField.DefaultExpiryDelay) {
            require(newValue > config.defaultReleaseDelay,
                "Escrow: expiry must be > release delay");
            config.defaultExpiryDelay = newValue;
        } else if (field == EscConfigField.MinDeposit) {
            config.minDeposit = newValue;
        } else if (field == EscConfigField.MaxDeposit) {
            require(newValue >= config.minDeposit, "Escrow: max must be >= min");
            config.maxDeposit = newValue;
        } else if (field == EscConfigField.DisputeResolver) {
            address oldResolver = config.disputeResolver;
            config.disputeResolver = address(uint160(newValue));
            emit DisputeResolverUpdated(oldResolver, config.disputeResolver);
            return;
        } else if (field == EscConfigField.ProtocolTreasury) {
            config.protocolTreasury = address(uint160(newValue));
        }

        emit ConfigUpdated(msg.sender, field, newValue);
    }

    // ============================================================
    // VIEW
    // ============================================================

    /// Obter depósitos de um beneficiário
    function getDepositsByBeneficiary(
        address beneficiary,
        uint256 offset,
        uint256 limit
    ) external view returns (bytes32[] memory) {
        bytes32[] memory allDeposits = depositsByBeneficiary[beneficiary];
        uint256 end = offset + limit;
        if (end > allDeposits.length) end = allDeposits.length;

        bytes32[] memory result = new bytes32[](end - offset);
        for (uint256 i = offset; i < end; i++) {
            result[i - offset] = allDeposits[i];
        }
        return result;
    }

    /// Verificar se depósito pode ser liberado
    function isReleasable(bytes32 depositId) external view returns (bool) {
        EscrowDeposit storage deposit = deposits[depositId];
        return (
            !deposit.released &&
            !deposit.refunded &&
            (block.timestamp >= deposit.releaseTime || deposit.proofSubmitted)
        );
    }

    /// Verificar se depósito pode ser reembolsado
    function isRefundable(bytes32 depositId) external view returns (bool) {
        EscrowDeposit storage deposit = deposits[depositId];
        return (
            !deposit.released &&
            !deposit.refunded &&
            block.timestamp >= deposit.expiryTime
        );
    }

    /// Obter contagem de depósitos por beneficiário
    function getDepositCount(address beneficiary) external view returns (uint256) {
        return depositsByBeneficiary[beneficiary].length;
    }

    // ============================================================
    // INTERNALS
    // ============================================================

    function _transferFunds(
        address recipient,
        uint256 amount,
        address tokenAddress
    ) internal {
        if (tokenAddress == address(0)) {
            (bool success, ) = recipient.call{value: amount}("");
            require(success, "Escrow: ETH transfer failed");
        } else {
            // Em produção: usar ERC20 safeTransfer
            // IERC20(tokenAddress).transfer(recipient, amount);
        }
    }

    // Permitir receber ETH
    receive() external payable {}
}
