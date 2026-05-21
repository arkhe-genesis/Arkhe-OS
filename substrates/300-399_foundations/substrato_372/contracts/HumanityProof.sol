// SPDX-License-Identifier: Apache-2.0
// Arkhe OS — Substrato 372: HumanityProof v1.0
// Canon: ∞.Ω.∇+++.372.humanity_proof_deployed

pragma solidity ^0.8.28;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "./interfaces/IInvariantGuard.sol";

contract HumanityToken is ERC20, Ownable {
    // Token de recompensa para ancoragem de humanidade
    constructor() ERC20("Humanity Token", "HUMAN") {}

    function mint(address to, uint256 amount) external onlyOwner {
        _mint(to, amount);
    }
}

contract HumanityProof is InvariantGuard, Ownable {
    HumanityToken public immutable humanToken;

    struct HumanProfile {
        uint256 startDay;           // Timestamp do Dia Zero
        uint256 commitmentCount;    // Contador incremental
        bytes32 latestCommitment;   // Último hash ancorado
        bool zkProofSubmitted;      // ZK-proof de humanidade gerado
        uint256 zkProofTimestamp;   // Quando a prova foi submetida
    }

    mapping(address => HumanProfile) public profiles;
    mapping(address => bytes32[]) public commitmentHistory;

    uint256 public constant MIN_DAYS_FOR_PROOF = 30; // Mínimo de dias para gerar ZK-proof

    event DailyCommitmentAnchored(address indexed human, uint256 day, bytes32 saltedHash);
    event ZKProofSubmitted(address indexed human, bytes32 proofHash, uint256 phiC);
    event HumanityTokensMinted(address indexed human, uint256 amount);

    constructor(address _humanToken) {
        humanToken = HumanityToken(_humanToken);
    }

    // Anchor diário: hash de interação pessoal + salt para privacidade
    function anchorDailyCommitment(bytes32 saltedHash) external aboveGhost(uint256(uint8(saltedHash[0])) * 10**16) {
        HumanProfile storage profile = profiles[msg.sender];

        if (profile.startDay == 0) {
            profile.startDay = block.timestamp;
        }

        uint256 day = profile.commitmentCount++;
        commitmentHistory[msg.sender].push(saltedHash);
        profile.latestCommitment = saltedHash;

        emit DailyCommitmentAnchored(msg.sender, day, saltedHash);

        // Faucet: recompensa diária por ancoragem consistente
        if (day < 7) {
            uint256 reward = 100 * 10**18 * (8 - day); // Decay reward: 700→600→...→100 HUMAN
            humanToken.mint(msg.sender, reward);
            emit HumanityTokensMinted(msg.sender, reward);
        }
    }

    // Submeter ZK-proof de humanidade (off-chain gerado, on-chain verificado)
    function submitHumanityZKProof(
        bytes32 proofHash,
        uint256 phiC,
        bytes calldata zkProof
    ) external aboveGhost(phiC) belowGap(phiC) {
        HumanProfile storage profile = profiles[msg.sender];

        require(profile.commitmentCount >= MIN_DAYS_FOR_PROOF, "Insufficient commitment days");
        require(!profile.zkProofSubmitted, "Proof already submitted");

        // Verificação simplificada da prova ZK (em produção: usar verifier contract)
        require(verifyZKProof(msg.sender, proofHash, zkProof), "Invalid ZK proof");

        profile.zkProofSubmitted = true;
        profile.zkProofTimestamp = block.timestamp;

        emit ZKProofSubmitted(msg.sender, proofHash, phiC);

        // Recompensa bônus por prova de humanidade verificada
        uint256 bonus = 1000 * 10**18; // 1000 HUMAN
        humanToken.mint(msg.sender, bonus);
        emit HumanityTokensMinted(msg.sender, bonus);
    }

    // Função auxiliar para verificação de ZK-proof (placeholder para integração Risc0/Starknet)
    function verifyZKProof(address /*human*/, bytes32 proofHash, bytes calldata zkProof)
        internal pure returns (bool)
    {
        // Em produção: chamar contrato verificador Risc0 ou Starknet
        // Por enquanto: verificação simplificada por hash
        return proofHash != bytes32(0) && zkProof.length > 0;
    }

    // Getters para frontend/dashboard
    function getHumanProfile(address human) external view returns (
        uint256 startDay,
        uint256 commitmentCount,
        bytes32 latestCommitment,
        bool zkProofSubmitted,
        uint256 humanTokenBalance
    ) {
        HumanProfile storage profile = profiles[human];
        return (
            profile.startDay,
            profile.commitmentCount,
            profile.latestCommitment,
            profile.zkProofSubmitted,
            humanToken.balanceOf(human)
        );
    }
}
