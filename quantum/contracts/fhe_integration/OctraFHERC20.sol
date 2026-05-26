// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;

import { FHERC20 } from "@fhenixprotocol/confidential-contracts/contracts/FHERC20/FHERC20.sol";
import { InEuint64 } from "@fhenixprotocol/cofhe-contracts/FHE.sol";

/**
 * @title OctraFHERC20
 * @dev FHERC20 customizado para bridge Octra HFHE ↔ Fhenix CoFHE
 * Implementa ERC-7984 com integração Circle Octra
 * Substrate 840+ — Token Module
 */
contract OctraFHERC20 is FHERC20 {

    // Mapping: Octra Circle ID → balanço cifrado bridgeado
    mapping(string => euint64) public circleBridgeBalances;

    // Mapping: Circle ID → indicador de atividade
    mapping(string => uint256) public circleIndicators;

    // Referência ao ACL Manager
    address public aclManager;

    // Taxa de bridge (2% para Royalty Catedral — Substrato 252)
    uint256 public constant BRIDGE_FEE_BPS = 200; // 2% = 200 basis points
    address public constant CATHEDRAL_TREASURY = 0x0000000000000000000000000000000000000000; // Endereço royalty placeholder

    // Níveis de permissão (espelhando ACL Manager)
    uint8 constant LEVEL_NONE = 0;      // Nenhum acesso
    uint8 constant LEVEL_THIS = 1;      // Apenas este contrato
    uint8 constant LEVEL_DELEGATED = 2;   // Endereços delegados
    uint8 constant LEVEL_DECRYPT = 3;    // Threshold Network
    uint8 constant LEVEL_PUBLIC = 4;     // Público

    function setAclManager(address _aclManager) external onlyOwner {
        aclManager = _aclManager;
    }

    // Eventos
    event CircleBridged(string circleId, uint64 amount, uint256 fhenixHandle);
    event CircleUnshielded(string circleId, uint64 plaintext, bytes thresholdSignature);
    event BridgeFeeCollected(string circleId, uint64 feeAmount);

    constructor() FHERC20("Octra Confidential Token", "OCTRA-F", 6) {}

    /**
     * @dev Bridge de tokens públicos para confidenciais (shield)
     * Usuário envia tokens ERC20 públicos, recebe FHERC20 cifrados
     */
    function shieldFromOctra(
        string calldata circleId,
        uint64 publicAmount
    ) external returns (euint64) {
        // 1. Recebe tokens públicos do usuário
        // Burn or pull public tokens from msg.sender
        _transfer(msg.sender, address(this), publicAmount);

        // 2. Converte para FHERC20 cifrado
        euint64 encryptedBalance = FHE.asEuint64(publicAmount);

        // 3. Aplica taxa de bridge (2% Royalty Catedral)
        euint64 fee = FHE.div(
            FHE.mul(encryptedBalance, FHE.asEuint64(BRIDGE_FEE_BPS)),
            FHE.asEuint64(10000)
        );
        euint64 netAmount = FHE.sub(encryptedBalance, fee);

        // 4. Atualiza balanço do Circle
        euint64 currentBalance = circleBridgeBalances[circleId];
        circleBridgeBalances[circleId] = FHE.add(currentBalance, netAmount);

        // 5. Registra fee para treasury
        // (implementação simplificada)

        // 6. Atualiza indicador
        _updateCircleIndicator(circleId, true);

        // 7. Configura ACL delegando ao ACL Manager
        uint256 handle = FHE.getHandle(circleBridgeBalances[circleId]);
        FHE.allowThis(handle);
        if (aclManager != address(0)) {
            FHE.allow(handle, aclManager);
        }

        emit CircleBridged(circleId, publicAmount, handle);
        return netAmount;
    }

    /**
     * @dev Transferência confidencial entre Circles Octra
     */
    function confidentialCircleTransfer(
        string calldata fromCircle,
        string calldata toCircle,
        InEuint64 memory encryptedAmount
    ) external returns (euint64) {
        // Verifica autorização no ACL Manager
        if (aclManager != address(0)) {
            (bool success, bytes memory data) = aclManager.staticcall(
                abi.encodeWithSignature("verifyAccess(uint256,address,string)",
                    FHE.getHandle(circleBridgeBalances[fromCircle]),
                    msg.sender,
                    fromCircle
                )
            );
            require(success && abi.decode(data, (bool)), "Not authorized to transfer from this circle");
        }

        euint64 amount = FHE.asEuint64(encryptedAmount);

        // Verifica balanço suficiente
        euint64 fromBalance = circleBridgeBalances[fromCircle];
        euint64 hasEnough = FHE.gte(fromBalance, amount);

        // Subtrai do sender (condicional — FHE select)
        euint64 newFromBalance = FHE.select(hasEnough, FHE.sub(fromBalance, amount), fromBalance);
        circleBridgeBalances[fromCircle] = newFromBalance;

        // Adiciona ao receiver (condicional — FHE select para evitar inflação)
        euint64 toBalance = circleBridgeBalances[toCircle];
        euint64 amountToTransfer = FHE.select(hasEnough, amount, FHE.asEuint64(0));
        circleBridgeBalances[toCircle] = FHE.add(toBalance, amountToTransfer);

        // Atualiza indicadores
        _updateCircleIndicator(fromCircle, false);
        _updateCircleIndicator(toCircle, true);

        return amount;
    }

    /**
     * @dev Unshield: converte FHERC20 cifrado para tokens públicos
     * Usa Threshold Network para decriptação verificável
     */
    function unshieldToOctra(
        string calldata circleId,
        uint64 plaintextAmount,
        bytes calldata thresholdSignature
    ) external {
        euint64 encBalance = circleBridgeBalances[circleId];
        uint256 handle = FHE.getHandle(encBalance);

        // Verifica autorização no ACL Manager
        if (aclManager != address(0)) {
            (bool success, bytes memory data) = aclManager.staticcall(
                abi.encodeWithSignature("verifyAccess(uint256,address,string)",
                    handle,
                    msg.sender,
                    circleId
                )
            );
            require(success && abi.decode(data, (bool)), "Not authorized to unshield this circle");
        }

        // 1. Verifica assinatura Threshold Network
        FHE.verifyDecryptResult(handle, plaintextAmount, thresholdSignature);

        // 2. Subtrai balanço cifrado
        euint64 amountToSubtract = FHE.asEuint64(plaintextAmount);
        euint64 newBalance = FHE.sub(encBalance, amountToSubtract);
        circleBridgeBalances[circleId] = newBalance;

        // 3. Envia tokens públicos para usuário
        _transfer(address(this), msg.sender, plaintextAmount);

        // 4. Atualiza indicador
        _updateCircleIndicator(circleId, false);

        emit CircleUnshielded(circleId, plaintextAmount, thresholdSignature);
    }

    /**
     * @dev Retorna indicador de atividade do Circle (compatibilidade ERC20)
     */
    function circleIndicatorOf(string calldata circleId) external view returns (uint256) {
        return circleIndicators[circleId];
    }

    /**
     * @dev Retorna balanço cifrado real (apenas para contratos autorizados)
     */
    function confidentialCircleBalance(string calldata circleId) external view returns (euint64) {
        return circleBridgeBalances[circleId];
    }

    /**
     * @dev Aplica permissões ACL para o handle do Circle interagindo com o ACL Manager
     * Este contrato (owner do ciphertext) deve chamar FHE.allow()
     */
    function applyCircleACL(string calldata circleId) external {
        require(aclManager != address(0), "ACL Manager not set");

        euint64 encBalance = circleBridgeBalances[circleId];
        uint256 handle = FHE.getHandle(encBalance);

        // Fetch permission level from ACL Manager
        (bool success, bytes memory data) = aclManager.staticcall(
            abi.encodeWithSignature("circlePermissionLevel(string)", circleId)
        );
        require(success, "Failed to fetch permission level");

        uint8 level = abi.decode(data, (uint8));

        if (level == LEVEL_NONE) {
            return;
        } else if (level == LEVEL_THIS) {
            FHE.allowThis(handle);
        } else if (level == LEVEL_DELEGATED) {
            FHE.allowThis(handle);
        } else if (level == LEVEL_DECRYPT) {
            FHE.allowThis(handle);
            FHE.allowForDecryption(handle);
        } else if (level == LEVEL_PUBLIC) {
            FHE.allowThis(handle);
            FHE.allowPublic(handle);
        }
    }

    /**
     * @dev Atualiza indicador de Circle
     */
    function _updateCircleIndicator(string memory circleId, bool received) internal {
        uint256 current = circleIndicators[circleId];
        if (current == 0) {
            // Primeira interação: 0.7984
            circleIndicators[circleId] = 7984;
        } else if (received) {
            // Recebimento: +0.0001
            circleIndicators[circleId] = current + 1;
        } else {
            // Envio: -0.0001
            if (current > 0) {
                circleIndicators[circleId] = current - 1;
            }
        }
    }

    /**
     * @dev Mint de tokens confidenciais (governança apenas)
     */
    function confidentialMint(
        address to,
        InEuint64 memory encryptedAmount
    ) external onlyOwner {
        euint64 amount = FHE.asEuint64(encryptedAmount);
        _mint(to, amount);
    }

    /**
     * @dev Override de _mint para suportar euint64
     */
    function _mint(address to, euint64 amount) internal {
        euint64 currentBalance = _confidentialBalances[to];
        _confidentialBalances[to] = FHE.add(currentBalance, amount);

        // Emite evento ERC20 compatível (without undefined indicators)
        emit Transfer(address(0), to, 0);
    }
}
