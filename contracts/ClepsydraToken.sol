// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title ClepsydraToken
 * @dev Token ERC-20 com atrito programado (hesitação) inspirado na Clepsydra do Casulo.
 * Representa Carats de um Diamond Standard Commodity específico.
 */
contract ClepsydraToken is ERC20, Ownable {
    using ECDSA for bytes32;

    // ============= ESTRUTURAS DE DADOS =============
    struct HesitationTransfer {
        address from;
        address to;
        uint256 amount;
        uint256 unlockBlock;
    }

    struct RedemptionRequest {
        address requester;
        uint256 amount;
        uint256 deadline;
        bool active;
    }

    // ============= VARIÁVEIS DE ESTADO =============
    uint256 public minHesitationBlocks = 10;   // ~2 minutos (Ethereum)
    uint256 public maxHesitationBlocks = 100;  // ~20 minutos
    uint256 public redemptionHesitationPeriod = 7 days;

    mapping(bytes32 => HesitationTransfer) public pendingTransfers;
    RedemptionRequest public currentRedemption;
    address public guardian;
    address public diamondChipAddress;
    uint256 public lastHealthReport;
    uint256 public constant HEALTH_REPORT_TIMEOUT = 24 hours;
    bool public tamperDetected;

    // ============= EVENTOS =============
    event TransferQueued(bytes32 indexed transferId, address from, address to, uint256 amount, uint256 unlockBlock);
    event TransferExecuted(bytes32 indexed transferId);
    event TransferCancelled(bytes32 indexed transferId);
    event HealthReported(uint256 timestamp);
    event TamperReported(address reporter, uint256 timestamp);
    event RedemptionRequested(address requester, uint256 amount, uint256 deadline);
    event RedemptionFinalized(address requester, uint256 amount);
    event RedemptionCancelled(string reason);

    // ============= CONSTRUTOR =============
    constructor(
        string memory name_,
        string memory symbol_,
        address _guardian,
        address _diamondChip,
        address initialOwner
    ) ERC20(name_, symbol_) Ownable(initialOwner) {
        guardian = _guardian;
        diamondChipAddress = _diamondChip;
        lastHealthReport = block.timestamp;
        _mint(initialOwner, 1_000_000 * 10 ** decimals());
    }

    // ============= MODIFICADORES =============
    modifier onlyGuardian() {
        require(msg.sender == guardian, "Apenas o Guardiao pode chamar");
        _;
    }

    modifier notTampered() {
        require(!tamperDetected, "Operacao bloqueada: tamper detectado");
        _;
    }

    modifier healthy() {
        require(block.timestamp - lastHealthReport <= HEALTH_REPORT_TIMEOUT, "Sistema sem prova de vida recente");
        _;
    }

    // ============= FUNÇÕES DE HESITAÇÃO (TRANSFER) =============

    function transferWithHesitation(address to, uint256 amount)
        external
        notTampered
        healthy
        returns (bytes32)
    {
        require(to != address(0), "Destinatario invalido");
        require(amount > 0, "Quantidade deve ser > 0");
        require(balanceOf(msg.sender) >= amount, "Saldo insuficiente");

        bytes32 transferId = keccak256(abi.encodePacked(msg.sender, to, amount, block.timestamp, block.number));
        uint256 hesitationBlocks = minHesitationBlocks +
            (uint256(keccak256(abi.encodePacked(transferId, blockhash(block.number - 1)))) %
             (maxHesitationBlocks - minHesitationBlocks + 1));
        uint256 unlockBlock = block.number + hesitationBlocks;

        _transfer(msg.sender, address(this), amount);

        pendingTransfers[transferId] = HesitationTransfer({
            from: msg.sender,
            to: to,
            amount: amount,
            unlockBlock: unlockBlock
        });

        emit TransferQueued(transferId, msg.sender, to, amount, unlockBlock);
        return transferId;
    }

    function finalizeTransfer(bytes32 transferId) external notTampered healthy {
        HesitationTransfer storage ht = pendingTransfers[transferId];
        require(ht.amount > 0, "Transferencia inexistente");
        require(block.number >= ht.unlockBlock, "Periodo de hesitacao nao concluido");

        _transfer(address(this), ht.to, ht.amount);
        emit TransferExecuted(transferId);
        delete pendingTransfers[transferId];
    }

    function cancelTransfer(bytes32 transferId) external {
        HesitationTransfer storage ht = pendingTransfers[transferId];
        require(ht.from == msg.sender, "Apenas o remetente pode cancelar");
        require(ht.amount > 0, "Transferencia inexistente");

        _transfer(address(this), ht.from, ht.amount);
        emit TransferCancelled(transferId);
        delete pendingTransfers[transferId];
    }

    // ============= FUNÇÕES DE AUDITORIA (GUARDIAN) =============

    function reportHealth() external onlyGuardian {
        lastHealthReport = block.timestamp;
        emit HealthReported(block.timestamp);
    }

    function reportTamper(string calldata message, bytes calldata signature) external {
        bytes32 ethSignedMessageHash = ECDSA.toEthSignedMessageHash(keccak256(bytes(message)));
        address signer = ECDSA.recover(ethSignedMessageHash, signature);
        require(signer == guardian, "Assinatura invalida: nao e o Guardiao");

        tamperDetected = true;
        emit TamperReported(signer, block.timestamp);

        if (currentRedemption.active) {
            currentRedemption.active = false;
            emit RedemptionCancelled("Tamper detectado durante redencao");
        }
    }

    // ============= FUNÇÕES DE REDENÇÃO =============

    function redeem(uint256 amount) external notTampered healthy {
        require(!currentRedemption.active, "Ja existe uma redencao em andamento");
        require(balanceOf(msg.sender) >= amount, "Saldo insuficiente");
        require(amount >= 100_000 * 10 ** decimals(), "Quantidade minima: 100.000 Carats");

        _transfer(msg.sender, address(this), amount);

        currentRedemption = RedemptionRequest({
            requester: msg.sender,
            amount: amount,
            deadline: block.timestamp + redemptionHesitationPeriod,
            active: true
        });

        emit RedemptionRequested(msg.sender, amount, currentRedemption.deadline);
    }

    function finalizeRedemption() external notTampered healthy {
        require(currentRedemption.active, "Nenhuma redencao ativa");
        require(block.timestamp >= currentRedemption.deadline, "Periodo de hesitacao nao concluido");

        uint256 amount = currentRedemption.amount;
        _burn(address(this), amount);

        emit RedemptionFinalized(currentRedemption.requester, amount);
        delete currentRedemption;
    }

    function cancelRedemption() external {
        require(currentRedemption.active, "Nenhuma redencao ativa");
        require(msg.sender == currentRedemption.requester || tamperDetected,
            "Apenas requerente ou em caso de tamper");

        _transfer(address(this), currentRedemption.requester, currentRedemption.amount);
        emit RedemptionCancelled("Cancelada");
        delete currentRedemption;
    }

    // ============= ADMIN =============

    function setGuardian(address newGuardian) external onlyOwner {
        guardian = newGuardian;
    }

    function setHesitationParams(uint256 _min, uint256 _max) external onlyOwner {
        require(_min <= _max, "Minimo deve ser <= maximo");
        minHesitationBlocks = _min;
        maxHesitationBlocks = _max;
    }

    function transfer(address to, uint256 amount) public override notTampered healthy returns (bool) {
        return super.transfer(to, amount);
    }

    function transferFrom(address from, address to, uint256 amount) public override notTampered healthy returns (bool) {
        return super.transferFrom(from, to, amount);
    }
}
