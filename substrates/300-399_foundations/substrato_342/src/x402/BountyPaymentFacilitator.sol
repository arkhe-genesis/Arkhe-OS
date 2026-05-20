// ═══════════════════════════════════════════════════════════════
// ARKHE OS — X402 PAYMENT FACILITATOR FOR BOUNTIES
// Canon: ∞.Ω.∇+++.342.x402_facilitator
// Integração com protocolo x402 para pagamento instantâneo em USDC.
// ═══════════════════════════════════════════════════════════════
pragma solidity ^0.8.28;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";

interface IX402Facilitator {
    function executePayment(
        address payer,
        address payee,
        uint256 amount,
        bytes calldata authorization
    ) external returns (bool);
}

contract BountyPaymentFacilitator {
    using ECDSA for bytes32;

    IERC20 public usdc; // USDC contract address
    IX402Facilitator public x402Facilitator;
    address public bountyRegistry;

    event PaymentExecuted(
        uint256 indexed bountyId,
        address indexed sponsor,
        address indexed assignee,
        uint256 amount,
        string x402TxHash
    );

    constructor(address _usdc, address _x402Facilitator, address _bountyRegistry) {
        usdc = IERC20(_usdc);
        x402Facilitator = IX402Facilitator(_x402Facilitator);
        bountyRegistry = _bountyRegistry;
    }

    function executeBountyPayment(
        uint256 bountyId,
        address sponsor,
        address assignee,
        uint256 amount,
        bytes calldata sponsorAuthorization
    ) external {
        require(msg.sender == bountyRegistry, "Only BountyRegistry can trigger payment");

        // Verificar autorização do sponsor via assinatura ECDSA
        bytes32 messageHash = keccak256(abi.encodePacked(bountyId, assignee, amount));
        address signer = messageHash.toEthSignedMessageHash().recover(sponsorAuthorization);
        require(signer == sponsor, "Invalid sponsor authorization");

        // Aprovar transferência de USDC para o facilitador x402
        usdc.approve(address(x402Facilitator), amount);

        // Executar pagamento via protocolo x402
        bool success = x402Facilitator.executePayment(
            sponsor,    // sponsor
            assignee,     // programador
            amount,       // em USDC (6 decimais)
            sponsorAuthorization
        );
        require(success, "x402 payment failed");

        emit PaymentExecuted(bountyId, sponsor, assignee, amount, "x402-tx-hash-placeholder");
    }
}
