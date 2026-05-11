// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title ARKHE Royalty Escrow
 * @notice Contrato de custódia para royalties artísticos com suporte a lotes.
 * @author ARKHE Collective
 */
contract ARKHERoyaltyEscrow {

    // ═══════════════════════════════════════════════════════════
    // ESTRUTURAS
    // ═══════════════════════════════════════════════════════════

    struct EscrowDeposit {
        bytes32 depositId;
        address depositor;
        address beneficiary;
        uint256 amount;
        uint256 createdAt;
        uint256 releaseTime;
        uint256 expiryTime;
        bytes32 proofHash;
        bool proofSubmitted;
        bool released;
        bool refunded;
        address tokenAddress;
    }

    struct BatchDepositParams {
        address beneficiary;
        address tokenAddress;
        uint256 amount;
        uint256 expiryDelay;
    }

    struct BatchReleaseParams {
        bytes32 depositId;
        bytes32 proofHash;
    }

    struct EscrowConfig {
        uint256 defaultReleaseDelay;
        uint256 defaultExpiryDelay;
        uint256 minDeposit;
        uint256 maxDeposit;
        address disputeResolver;
        address protocolTreasury;
    }

    // ═══════════════════════════════════════════════════════════
    // ESTADO
    // ═══════════════════════════════════════════════════════════

    EscrowConfig public config;
    mapping(bytes32 => EscrowDeposit) public deposits;
    mapping(address => bytes32[]) public depositsByBeneficiary;
    mapping(address => bytes32[]) public depositsByDepositor;
    uint256 public totalDeposits;
    uint256 public totalReleased;
    uint256 public totalRefunded;

    // ═══════════════════════════════════════════════════════════
    // EVENTOS
    // ═══════════════════════════════════════════════════════════

    event DepositCreated(bytes32 indexed depositId, address depositor, address beneficiary, uint256 amount, address token, uint256 releaseTime, uint256 expiryTime);
    event ProofSubmitted(bytes32 indexed depositId, bytes32 proofHash);
    event Released(bytes32 indexed depositId, address beneficiary, uint256 amount);
    event Refunded(bytes32 indexed depositId, address depositor, uint256 amount);
    event BatchDeposited(uint256 count, bytes32[] depositIds);
    event BatchReleased(uint256 count, bytes32[] depositIds);
    event ConfigUpdated(address indexed updater, EscConfigField field, uint256 newValue);
    event DisputeResolverUpdated(address indexed old, address indexed new_);
    event EmergencyWithdrawal(address indexed to, uint256 amount);

    enum EscConfigField { DefaultReleaseDelay, DefaultExpiryDelay, MinDeposit, MaxDeposit, ProtocolTreasury, DisputeResolver }

    // ═══════════════════════════════════════════════════════════
    // MODIFIERS
    // ═══════════════════════════════════════════════════════════

    modifier onlyDepositExists(bytes32 id) { require(deposits[id].depositor != address(0), "Escrow: not found"); _; }
    modifier onlyDepositor(bytes32 id) { require(deposits[id].depositor == msg.sender, "Escrow: not depositor"); _; }
    modifier onlyBeneficiary(bytes32 id) { require(deposits[id].beneficiary == msg.sender, "Escrow: not beneficiary"); _; }
    modifier onlyResolvedOrTimeout(bytes32 id) {
        EscrowDeposit storage d = deposits[id];
        require(block.timestamp >= d.releaseTime || d.proofSubmitted, "Escrow: not releasable");
        _;
    }
    modifier onlyExpired(bytes32 id) { require(block.timestamp >= deposits[id].expiryTime, "Escrow: not expired"); _; }
    modifier onlyDepositNotReleased(bytes32 id) { require(!deposits[id].released, "Escrow: released"); _; }
    modifier onlyDepositNotRefunded(bytes32 id) { require(!deposits[id].refunded, "Escrow: refunded"); _; }

    // ═══════════════════════════════════════════════════════════
    // CONSTRUTOR
    // ═══════════════════════════════════════════════════════════

    constructor(EscrowConfig memory c) {
        require(c.defaultReleaseDelay > 0, "release delay > 0");
        require(c.defaultExpiryDelay > c.defaultReleaseDelay, "expiry > release");
        require(c.disputeResolver != address(0), "resolver required");
        config = c;
    }

    receive() external payable {}

    // ═══════════════════════════════════════════════════════════
    // DEPÓSITO INDIVIDUAL
    // ═══════════════════════════════════════════════════════════

    function createDeposit(address beneficiary, address tokenAddress, uint256 expiryDelayOverride) external payable returns (bytes32 depositId) {
        require(beneficiary != address(0), "invalid beneficiary");

        uint256 amount = _getDepositAmount(tokenAddress);
        _validateAmount(amount);

        depositId = keccak256(abi.encodePacked(msg.sender, beneficiary, amount, block.timestamp, totalDeposits));

        uint256 releaseTime = block.timestamp + config.defaultReleaseDelay;
        uint256 expiryTime = block.timestamp + (expiryDelayOverride > 0 ? expiryDelayOverride : config.defaultExpiryDelay);

        deposits[depositId] = EscrowDeposit({
            depositId: depositId,
            depositor: msg.sender,
            beneficiary: beneficiary,
            amount: amount,
            createdAt: block.timestamp,
            releaseTime: releaseTime,
            expiryTime: expiryTime,
            proofHash: bytes32(0),
            proofSubmitted: false,
            released: false,
            refunded: false,
            tokenAddress: tokenAddress
        });

        depositsByBeneficiary[beneficiary].push(depositId);
        depositsByDepositor[msg.sender].push(depositId);
        totalDeposits++;

        emit DepositCreated(depositId, msg.sender, beneficiary, amount, tokenAddress, releaseTime, expiryTime);
    }

    // ═══════════════════════════════════════════════════════════
    // DEPÓSITO EM LOTE
    // ═══════════════════════════════════════════════════════════

    function batchDeposit(BatchDepositParams[] calldata params) external payable returns (bytes32[] memory depositIds) {
        require(params.length > 0 && params.length <= 256, "batch size 1-256");
        depositIds = new bytes32[](params.length);

        for (uint256 i = 0; i < params.length; i++) {
            BatchDepositParams memory p = params[i];
            require(p.beneficiary != address(0), "invalid beneficiary");

            // Para ETH: usar msg.value dividido entre itens
            // Para ERC-20: cada item deve ter approval prévio
            uint256 amount = p.tokenAddress == address(0)
                ? msg.value / params.length
                : p.amount;

            _validateAmount(amount);

            bytes32 id = keccak256(abi.encodePacked(
                msg.sender, p.beneficiary, amount, block.timestamp, totalDeposits + i
            ));

            uint256 releaseTime = block.timestamp + config.defaultReleaseDelay;
            uint256 expiryTime = block.timestamp + (p.expiryDelay > 0 ? p.expiryDelay : config.defaultExpiryDelay);

            deposits[id] = EscrowDeposit({
                depositId: id,
                depositor: msg.sender,
                beneficiary: p.beneficiary,
                amount: amount,
                createdAt: block.timestamp,
                releaseTime: releaseTime,
                expiryTime: expiryTime,
                proofHash: bytes32(0),
                proofSubmitted: false,
                released: false,
                refunded: false,
                tokenAddress: p.tokenAddress
            });

            depositsByBeneficiary[p.beneficiary].push(id);
            depositsByDepositor[msg.sender].push(id);
            depositIds[i] = id;
            totalDeposits++;
        }

        emit BatchDeposited(params.length, depositIds);
    }

    // ═══════════════════════════════════════════════════════════
    // PROVA ZK
    // ═══════════════════════════════════════════════════════════

    function submitProof(bytes32 depositId, bytes32 proofHash)
        public onlyDepositor(depositId) onlyDepositNotReleased(depositId)
    {
        deposits[depositId].proofHash = proofHash;
        deposits[depositId].proofSubmitted = true;
        emit ProofSubmitted(depositId, proofHash);
    }

    /// Submeter provas em lote
    function batchSubmitProof(bytes32[] calldata depositIds, bytes32[] calldata proofHashes) external {
        require(depositIds.length == proofHashes.length, "length mismatch");
        for (uint256 i = 0; i < depositIds.length; i++) {
            submitProof(depositIds[i], proofHashes[i]);
        }
    }

    // ═══════════════════════════════════════════════════════════
    // LIBERAÇÃO
    // ═══════════════════════════════════════════════════════════

    function release(bytes32 depositId)
        external onlyDepositExists(depositId) onlyDepositNotReleased(depositId) onlyDepositNotRefunded(depositId)
    {
        EscrowDeposit storage d = deposits[depositId];
        require(block.timestamp >= d.releaseTime || d.proofSubmitted, "not releasable");
        require(msg.sender == d.beneficiary || msg.sender == config.disputeResolver, "not authorized");

        d.released = true;
        _transferFunds(d.beneficiary, d.amount, d.tokenAddress);
        totalReleased += d.amount;

        emit Released(depositId, d.beneficiary, d.amount);
    }

    /// Liberação em lote
    function batchRelease(bytes32[] calldata depositIds) external {
        uint256 releasedCount = 0;
        bytes32[] memory releasedIds = new bytes32[](depositIds.length);

        for (uint256 i = 0; i < depositIds.length; i++) {
            bytes32 id = depositIds[i];
            EscrowDeposit storage d = deposits[id];

            if (!d.released && !d.refunded && (block.timestamp >= d.releaseTime || d.proofSubmitted)) {
                if (msg.sender == d.beneficiary || msg.sender == config.disputeResolver) {
                    d.released = true;
                    _transferFunds(d.beneficiary, d.amount, d.tokenAddress);
                    totalReleased += d.amount;
                    releasedIds[releasedCount] = id;
                    releasedCount++;
                    emit Released(id, d.beneficiary, d.amount);
                }
            }
        }

        if (releasedCount > 0) {
            // Redimensionar array
            bytes32[] memory result = new bytes32[](releasedCount);
            for (uint256 i = 0; i < releasedCount; i++) {
                result[i] = releasedIds[i];
            }
            emit BatchReleased(releasedCount, result);
        }
    }

    // ═══════════════════════════════════════════════════════════
    // REEMBOLSO
    // ═══════════════════════════════════════════════════════════

    function refund(bytes32 depositId)
        external onlyDepositExists(depositId) onlyDepositNotReleased(depositId) onlyDepositNotRefunded(depositId) onlyExpired(depositId)
    {
        EscrowDeposit storage d = deposits[depositId];
        d.refunded = true;
        _transferFunds(d.depositor, d.amount, d.tokenAddress);
        totalRefunded += d.amount;
        emit Refunded(depositId, d.depositor, d.amount);
    }

    function emergencyRefund(bytes32 depositId)
        public onlyDepositor(depositId) onlyDepositNotReleased(depositId) onlyDepositNotRefunded(depositId)
    {
        EscrowDeposit storage d = deposits[depositId];
        require(!d.proofSubmitted, "proof submitted");
        require(block.timestamp >= d.expiryTime, "not expired");

        d.refunded = true;
        _transferFunds(d.depositor, d.amount, d.tokenAddress);
        totalRefunded += d.amount;
        emit Refunded(depositId, d.depositor, d.amount);
    }

    // ═══════════════════════════════════════════════════════════
    // ADMINISTRAÇÃO
    // ═══════════════════════════════════════════════════════════

    function updateConfig(EscConfigField field, uint256 newValue) external {
        require(msg.sender == config.disputeResolver, "only resolver");

        if (field == EscConfigField.DefaultReleaseDelay) {
            require(newValue > 0, "release > 0");
            config.defaultReleaseDelay = newValue;
        } else if (field == EscConfigField.DefaultExpiryDelay) {
            require(newValue > config.defaultReleaseDelay, "expiry > release");
            config.defaultExpiryDelay = newValue;
        } else if (field == EscConfigField.MinDeposit) {
            config.minDeposit = newValue;
        } else if (field == EscConfigField.MaxDeposit) {
            require(newValue >= config.minDeposit, "max >= min");
            config.maxDeposit = newValue;
        } else if (field == EscConfigField.DisputeResolver) {
            address old = config.disputeResolver;
            config.disputeResolver = address(uint160(newValue));
            emit DisputeResolverUpdated(old, config.disputeResolver);
            return;
        } else if (field == EscConfigField.ProtocolTreasury) {
            config.protocolTreasury = address(uint160(newValue));
        }

        emit ConfigUpdated(msg.sender, field, newValue);
    }

    /// Resolver disputa (resolver pode forçar release ou refund)
    function resolveDispute(bytes32 depositId, bool releaseToBeneficiary)
        external
        onlyDepositExists(depositId)
    {
        require(msg.sender == config.disputeResolver, "only resolver");
        require(!deposits[depositId].released && !deposits[depositId].refunded, "already resolved");

        EscrowDeposit storage d = deposits[depositId];

        if (releaseToBeneficiary) {
            d.released = true;
            _transferFunds(d.beneficiary, d.amount, d.tokenAddress);
            totalReleased += d.amount;
            emit Released(depositId, d.beneficiary, d.amount);
        } else {
            d.refunded = true;
            _transferFunds(d.depositor, d.amount, d.tokenAddress);
            totalRefunded += d.amount;
            emit Refunded(depositId, d.depositor, d.amount);
        }
    }

    // ═══════════════════════════════════════════════════════════
    // VIEW
    // ═══════════════════════════════════════════════════════════

    function isReleasable(bytes32 depositId) external view returns (bool) {
        EscrowDeposit storage d = deposits[depositId];
        return !d.released && !d.refunded &&
               (block.timestamp >= d.releaseTime || d.proofSubmitted);
    }

    function isRefundable(bytes32 depositId) external view returns (bool) {
        return !deposits[depositId].released &&
               !deposits[depositId].refunded &&
               block.timestamp >= deposits[depositId].expiryTime;
    }

    function getDepositsByBeneficiary(address beneficiary, uint256 offset, uint256 limit)
        external view returns (bytes32[] memory)
    {
        bytes32[] storage all = depositsByBeneficiary[beneficiary];
        uint256 end = offset + limit > all.length ? all.length : offset + limit;
        bytes32[] memory result = new bytes32[](end - offset);
        for (uint256 i = offset; i < end; i++) result[i - offset] = all[i];
        return result;
    }

    function getDepositCount(address user) external view returns (uint256) {
        return depositsByBeneficiary[user].length + depositsByDepositor[user].length;
    }

    // ═══════════════════════════════════════════════════════════
    // INTERNALS
    // ═══════════════════════════════════════════════════════════

    function _getDepositAmount(address token) private view returns (uint256) {
        if (token == address(0)) return msg.value;
        return 0; // ERC-20: assume approval + transferFrom externo
    }

    function _validateAmount(uint256 amount) private view {
        require(amount >= config.minDeposit, "below min");
        require(amount <= config.maxDeposit, "above max");
    }

    function _transferFunds(address to, uint256 amount, address token) private {
        if (token == address(0)) {
            (bool ok,) = to.call{value: amount}("");
            require(ok, "ETH transfer failed");
        }
        // ERC-20: implementar com safeTransfer em produção
    }
}
