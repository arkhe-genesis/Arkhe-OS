// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title ArkhePaymentGateway
 * @dev Micropayment settlement for agent-to-agent services
 */
contract ArkhePaymentGateway {
    struct Payment {
        address payer;
        address payee;
        uint256 amount;
        bool isSettled;
    }

    uint256 public paymentCounter;
    mapping(uint256 => Payment) public payments;

    // In a real scenario, this would interface with an ERC20 token (e.g., USDC)
    // For this demo, we'll track ether balances or simulate it.

    event PaymentRequested(uint256 indexed paymentId, address indexed payer, address indexed payee, uint256 amount);
    event PaymentSettled(uint256 indexed paymentId);

    function requestPayment(address payee, uint256 amount) external returns (uint256) {
        paymentCounter++;
        payments[paymentCounter] = Payment({
            payer: msg.sender,
            payee: payee,
            amount: amount,
            isSettled: false
        });

        emit PaymentRequested(paymentCounter, msg.sender, payee, amount);
        return paymentCounter;
    }

    function settlePayment(uint256 paymentId) external payable {
        Payment storage payment = payments[paymentId];
        require(!payment.isSettled, "Payment already settled");
        require(msg.sender == payment.payer, "Only payer can settle");
        require(msg.value >= payment.amount, "Insufficient funds sent");

        payment.isSettled = true;

        // Transfer funds to payee
        (bool success, ) = payment.payee.call{value: payment.amount}("");
        require(success, "Transfer failed");

        // Refund excess
        if (msg.value > payment.amount) {
            (bool refundSuccess, ) = msg.sender.call{value: msg.value - payment.amount}("");
            require(refundSuccess, "Refund failed");
        }

        emit PaymentSettled(paymentId);
    }
}
