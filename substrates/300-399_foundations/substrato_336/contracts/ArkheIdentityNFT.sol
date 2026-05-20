// SPDX-License-Identifier: Apache-2.0
// ═══════════════════════════════════════════════════════════════
// ARKHE OS — ORKUT 2.0 IDENTITY NFT (ERC‑721)
// Canon: ∞.Ω.∇+++.336.identity_nft
// Vincula ORCID a um NFT soberano. Apenas o detentor do ORCID
// (verificado por um oráculo) pode mintar seu próprio token.
// ═══════════════════════════════════════════════════════════════
pragma solidity ^0.8.28;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";

contract ArkheIdentityNFT is ERC721Enumerable {
    using ECDSA for bytes32;

    uint256 public tokenCounter;
    mapping(bytes32 => bool) public orcidClaimed;  // hash(orcid) -> bool
    mapping(uint256 => bytes32) public tokenToOrcidHash;
    mapping(uint256 => uint256) public tokenToPhiC; // Φ_C × 10⁶

    address public oracleAddress;  // endereço que verifica assinatura ORCID

    event IdentityMinted(uint256 indexed tokenId, address indexed owner, bytes32 indexed orcidHash);
    event PhiCUpdated(uint256 indexed tokenId, uint256 newPhiC);

    constructor(address _oracle) ERC721("Arkhe Identity", "AID") {
        oracleAddress = _oracle;
    }

    function mintIdentity(
        bytes32 orcidHash,
        bytes calldata oracleSignature  // assinatura do oráculo sobre (orcidHash, msg.sender)
    ) external returns (uint256) {
        require(!orcidClaimed[orcidHash], "ORCID already claimed");
        // Verificar assinatura do oráculo
        bytes32 messageHash = keccak256(abi.encodePacked(orcidHash, msg.sender));
        address signer = messageHash.toEthSignedMessageHash().recover(oracleSignature);
        require(signer == oracleAddress, "Invalid oracle signature");

        uint256 tokenId = ++tokenCounter;
        _safeMint(msg.sender, tokenId);
        orcidClaimed[orcidHash] = true;
        tokenToOrcidHash[tokenId] = orcidHash;
        tokenToPhiC[tokenId] = 577350269; // Ghost × 10⁹

        emit IdentityMinted(tokenId, msg.sender, orcidHash);
        return tokenId;
    }

    function updatePhiC(uint256 tokenId, uint256 newPhiC) external {
        // Apenas um feed oracle aprovado pode atualizar Φ_C
        require(msg.sender == oracleAddress, "Only oracle can update Phi_C");
        require(newPhiC < 10**9, "Phi_C must be < 1.0");
        tokenToPhiC[tokenId] = newPhiC;
        emit PhiCUpdated(tokenId, newPhiC);
    }
}
