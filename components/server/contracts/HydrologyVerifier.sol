// HydrologyVerifier.sol - Verificação On-Chain de Provas ZK de Balanço Hídrico

pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/AccessControl.sol";

interface IGroth16Verifier {
    function verifyProof(
        uint256[2] calldata a,
        uint256[2][2] calldata b,
        uint256[2] calldata c,
        uint256[] calldata input
    ) external view returns (bool);
}

contract HydrologyVerifier is AccessControl {
    bytes32 public constant VALIDATOR_ROLE = keccak256("VALIDATOR_ROLE");
    
    IGroth16Verifier public groth16;
    
    // Mapeamento de nullifiers gastos para prevenir replay attacks
    mapping(uint256 => bool) public spentNullifiers;
    
    // Registro público do status de sustentabilidade por bacia
    mapping(uint256 => bool) public basinSustainabilityStatus;
    mapping(uint256 => uint256) public lastProofTimestamp;
    
    event WaterBalanceVerified(
        uint256 indexed basinHash,
        uint256 indexed nullifier,
        bool isSustainable,
        uint256 timestamp
    );
    
    event BasinSustainabilityChanged(
        uint256 indexed basinHash,
        bool isSustainable
    );
    
    constructor(address _groth16) {
        groth16 = IGroth16Verifier(_groth16);
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
    }
    
    function verifyWaterBalanceProof(
        uint256 basinHash,
        uint256[2] calldata a,
        uint256[2][2] calldata b,
        uint256[2] calldata c,
        uint256[] calldata publicInputs
    ) external onlyRole(VALIDATOR_ROLE) returns (bool) {
        // publicInputs: [basin_hash, timestamp, safety_threshold, is_valid, nullifier, merkle_root]
        require(publicInputs.length >= 6, "Invalid inputs");
        
        uint256 inputBasinHash = publicInputs[0];
        uint256 nullifier = publicInputs[4];
        bool isSustainable = publicInputs[3] == 1;
        
        require(inputBasinHash == basinHash, "Basin hash mismatch");
        
        // Verifica nullifier não gasto
        require(!spentNullifiers[nullifier], "Nullifier already spent");
        
        // Verifica prova criptográfica
        bool isValid = groth16.verifyProof(a, b, c, publicInputs);
        require(isValid, "Invalid ZK proof");
        
        // Marca nullifier como gasto
        spentNullifiers[nullifier] = true;
        
        // Atualiza status da bacia
        bool oldStatus = basinSustainabilityStatus[basinHash];
        basinSustainabilityStatus[basinHash] = isSustainable;
        lastProofTimestamp[basinHash] = block.timestamp;
        
        if (oldStatus != isSustainable) {
            emit BasinSustainabilityChanged(basinHash, isSustainable);
        }
        
        emit WaterBalanceVerified(basinHash, nullifier, isSustainable, block.timestamp);
        
        return true;
    }
    
    // Função para consultar status de sustentabilidade
    function getBasinStatus(uint256 basinHash) external view returns (
        bool isSustainable,
        bool isExpired
    ) {
        isSustainable = basinSustainabilityStatus[basinHash];
        // Provas expiram após 24 horas (86400 segundos)
        isExpired = (block.timestamp - lastProofTimestamp[basinHash]) > 86400;
    }
}
