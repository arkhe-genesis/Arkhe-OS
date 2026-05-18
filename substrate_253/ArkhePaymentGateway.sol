// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title ArkhePaymentGateway
 * @notice Implements x402 payment protocol for agent‑to‑agent micropayments
 * @dev Integrates with USDC for payments and ERC‑8004 for identity
 */
contract ArkhePaymentGateway {

    IERC20 public usdcToken;
    ArkheIdentity public identityRegistry;

    struct Payment {
        bytes32 paymentId;
        address payer;
        address payee;
        uint256 amount;          // In USDC (6 decimals)
        string serviceType;      // "parsing", "verification", "computation"
        bytes32 serviceHash;     // SHA3‑256 of the service performed
        uint256 timestamp;
        bool settled;
    }

    mapping(bytes32 => Payment) public payments;

    event PaymentRequested(bytes32 indexed paymentId, address payer, address payee, uint256 amount);
    event PaymentSettled(bytes32 indexed paymentId, uint256 timestamp);

    constructor(address _usdcToken, address _identityRegistry) {
        usdcToken = IERC20(_usdcToken);
        identityRegistry = ArkheIdentity(_identityRegistry);
    }

    function requestPayment(
        address _payee,
        uint256 _amount,
        string calldata _serviceType,
        bytes32 _serviceHash
    ) external returns (bytes32) {
        require(identityRegistry.isActive(msg.sender), "Payer identity not active");
        require(identityRegistry.isActive(_payee), "Payee identity not active");

        bytes32 paymentId = keccak256(abi.encodePacked(
            msg.sender, _payee, _amount, _serviceHash, block.timestamp
        ));

        payments[paymentId] = Payment({
            paymentId: paymentId,
            payer: msg.sender,
            payee: _payee,
            amount: _amount,
            serviceType: _serviceType,
            serviceHash: _serviceHash,
            timestamp: block.timestamp,
            settled: false
        });

        emit PaymentRequested(paymentId, msg.sender, _payee, _amount);
        return paymentId;
    }

    function settlePayment(bytes32 _paymentId) external {
        Payment storage payment = payments[_paymentId];
        require(payment.settled == false, "Already settled");
        require(msg.sender == payment.payer, "Only payer can settle");

        // Transfer USDC from payer to payee
        require(usdcToken.transferFrom(payment.payer, payment.payee, payment.amount), "Transfer failed");

        payment.settled = true;
        emit PaymentSettled(_paymentId, block.timestamp);
    }

    function getPayment(bytes32 _paymentId) external view returns (Payment memory) {
        return payments[_paymentId];
    }
}

interface IERC20 {
    function transferFrom(address sender, address recipient, uint256 amount) external returns (bool);
}

interface ArkheIdentity {
    function isActive(address _owner) external view returns (bool);
}