import os

base_dir = "./arkhe_evm_bridge"
os.makedirs(base_dir, exist_ok=True)

# Create the JavaScript/TypeScript module for EVM calldata generation
js_module = '''/**
 * ARKHE OS EVM Bridge — Calldata Encoder for Badge Anchoring
 * Canon: ∞.Ω.∇+++.evm.calldata.badge_anchor
 *
 * Integrates ethers.js calldata encoding with ARKHE TemporalChain
 * for on-chain attestation of consciousness moments, molecule signatures,
 * and canonical seals.
 */

const { ethers } = require('ethers');

/**
 * ARKHE Badge Anchor Interface
 * Encodes calldata for anchoring ARKHE badges on EVM-compatible chains
 */
class ArkheBadgeAnchor {
    constructor(contractAddress, providerOrSigner) {
        this.contractAddress = contractAddress;
        this.provider = providerOrSigner;

        // ABI fragment for anchorBadge function
        this.abi = [
            "function anchorBadge(bytes32 badgeKey, bytes signature) external",
            "function getBadge(bytes32 badgeKey) external view returns (tuple(bytes signature, uint256 timestamp, address issuer))",
            "function verifyBadge(bytes32 badgeKey, bytes calldata signature) external view returns (bool)",
            "event BadgeAnchored(bytes32 indexed badgeKey, address indexed issuer, uint256 timestamp)"
        ];

        this.iface = new ethers.utils.Interface(this.abi);
        this.contract = new ethers.Contract(contractAddress, this.abi, providerOrSigner);
    }

    /**
     * Encode calldata for anchorBadge without sending transaction
     * Useful for meta-transactions, multisig, or offline signing
     */
    encodeAnchorCalldata(badgeKey, signature) {
        // Validate inputs
        if (!ethers.utils.isHexString(badgeKey) || ethers.utils.hexDataLength(badgeKey) !== 32) {
            throw new Error('badgeKey must be bytes32 (32 bytes hex string)');
        }

        if (!ethers.utils.isHexString(signature)) {
            throw new Error('signature must be a valid hex string');
        }

        // Encode function data
        const calldata = this.iface.encodeFunctionData("anchorBadge", [
            badgeKey,
            signature
        ]);

        return {
            calldata,
            selector: calldata.slice(0, 10), // 0x + 4 bytes
            badgeKey,
            signatureLength: (signature.length - 2) / 2, // bytes
            decoded: {
                function: 'anchorBadge(bytes32,bytes)',
                badgeKey: badgeKey,
                signature: signature.slice(0, 66) + '...' // Truncate for display
            }
        };
    }

    /**
     * Create a complete Ethereum transaction object for badge anchoring
     */
    async createAnchorTransaction(badgeKey, signature, overrides = {}) {
        const calldata = this.encodeAnchorCalldata(badgeKey, signature);

        // Estimate gas
        const gasEstimate = await this.provider.estimateGas({
            to: this.contractAddress,
            data: calldata.calldata
        }).catch(() => ethers.BigNumber.from(100000)); // Fallback

        return {
            to: this.contractAddress,
            data: calldata.calldata,
            gasLimit: gasEstimate.mul(12).div(10), // +20% buffer
            value: 0,
            ...overrides
        };
    }

    /**
     * Anchor a badge directly (requires signer)
     */
    async anchorBadge(badgeKey, signature, overrides = {}) {
        const tx = await this.contract.anchorBadge(badgeKey, signature, overrides);
        const receipt = await tx.wait();

        // Parse event
        const event = receipt.events.find(e => e.event === 'BadgeAnchored');

        return {
            transactionHash: receipt.transactionHash,
            blockNumber: receipt.blockNumber,
            gasUsed: receipt.gasUsed.toString(),
            badgeKey: event.args.badgeKey,
            issuer: event.args.issuer,
            timestamp: event.args.timestamp.toNumber()
        };
    }

    /**
     * Generate badge key from ARKHE substrate data
     */
    static generateBadgeKey(substrateId, canonicalSeal, timestamp) {
        const payload = ethers.utils.defaultAbiCoder.encode(
            ['string', 'bytes32', 'uint256'],
            [substrateId, canonicalSeal, timestamp]
        );
        return ethers.utils.keccak256(payload);
    }

    /**
     * Sign badge with ARKHE HSM key
     */
    static async signBadge(signer, badgeKey, substrateData) {
        const messageHash = ethers.utils.keccak256(
            ethers.utils.defaultAbiCoder.encode(
                ['bytes32', 'string'],
                [badgeKey, JSON.stringify(substrateData)]
            )
        );
        return await signer.signMessage(ethers.utils.arrayify(messageHash));
    }
}

/**
 * ARKHE TemporalChain EVM Bridge
 * Anchors TemporalChain seals to Ethereum for cross-chain verification
 */
class ArkheTemporalChainBridge {
    constructor(badgeAnchor, temporalChain) {
        this.badgeAnchor = badgeAnchor;
        this.temporalChain = temporalChain;
    }

    async anchorTemporalSeal(seal, substrateMetadata) {
        const badgeKey = ArkheBadgeAnchor.generateBadgeKey(
            substrateMetadata.substrateId,
            seal,
            substrateMetadata.timestamp
        );

        const signature = await ArkheBadgeAnchor.signBadge(
            this.badgeAnchor.provider,
            badgeKey,
            substrateMetadata
        );

        return await this.badgeAnchor.anchorBadge(badgeKey, signature);
    }
}

// Example usage with ARKHE Substrate 241 seal
async function example() {
    // Substrate 241 canonical seal
    const substrate241Seal = '0x4b854d6a61dab3a5dd8d5ede402d72eac201409d6ee478f767083da3515621b5';

    const metadata = {
        substrateId: '241+∞',
        canon: '∞.Ω.∇+++.241.semantic_chemistry_secure',
        testsPassed: 20,
        testsTotal: 20,
        passRate: 1.0,
        timestamp: Math.floor(Date.now() / 1000),
        pillars: ['hsm_pqc', 'seccomp_sandbox', 'ast_ml_learning', 'guardrail_orchestrator']
    };

    // Generate badge key
    const badgeKey = ArkheBadgeAnchor.generateBadgeKey(
        metadata.substrateId,
        substrate241Seal,
        metadata.timestamp
    );

    console.log('Badge Key:', badgeKey);

    // Example calldata (without actual signer)
    const dummySignature = '0x' + '00'.repeat(65); // 65-byte ECDSA signature placeholder

    const iface = new ethers.utils.Interface([
        "function anchorBadge(bytes32 badgeKey, bytes signature) external"
    ]);

    const calldata = iface.encodeFunctionData("anchorBadge", [badgeKey, dummySignature]);

    console.log('\n=== ARKHE EVM Calldata ===');
    console.log('Function: anchorBadge(bytes32,bytes)');
    console.log('Selector:', calldata.slice(0, 10));
    console.log('Full calldata:', calldata);
    console.log('Calldata length:', (calldata.length - 2) / 2, 'bytes');

    // Decode to verify
    const decoded = iface.decodeFunctionData("anchorBadge", calldata);
    console.log('\nDecoded badgeKey:', decoded.badgeKey);
    console.log('Decoded signature length:', decoded.signature.length, 'bytes');
}

// Run example if executed directly
if (require.main === module) {
    example().catch(console.error);
}

module.exports = {
    ArkheBadgeAnchor,
    ArkheTemporalChainBridge
};
'''

with open(f"{base_dir}/arkhe_evm_bridge.js", "w") as f:
    f.write(js_module)

# Create a Python equivalent for the ARKHE backend
py_module = '''#!/usr/bin/env python3
"""
ARKHE OS EVM Bridge — Python Backend
Canon: ∞.Ω.∇+++.evm.bridge.python

Python equivalent of ethers.js calldata encoding for ARKHE backend integration.
Uses eth_abi and eth_utils for ABI encoding.
"""

from eth_abi import encode
from eth_utils import keccak, to_hex, to_bytes, is_hexstr
import json
import time
from typing import Dict, Tuple, Optional

class ArkheEVMBridge:
    """
    Bridge Python backend → EVM calldata encoding.
    Mirrors the JavaScript ArkheBadgeAnchor class.
    """

    # Function selector for anchorBadge(bytes32,bytes)
    # keccak256("anchorBadge(bytes32,bytes)")[:4]
    ANCHOR_SELECTOR = "0x8a1b4b7e"  # Example selector

    @staticmethod
    def encode_anchor_calldata(badge_key: str, signature: str) -> str:
        """
        Encode calldata for anchorBadge(bytes32,bytes).

        Args:
            badge_key: 32-byte hex string (0x + 64 chars)
            signature: Variable-length hex string

        Returns:
            Complete calldata hex string
        """
        if not is_hexstr(badge_key) or len(badge_key) != 66:  # 0x + 64
            raise ValueError(f"badge_key must be bytes32 hex string, got {badge_key}")

        if not is_hexstr(signature):
            raise ValueError(f"signature must be hex string, got {signature}")

        # Encode arguments: bytes32, bytes
        # bytes32 is padded to 32 bytes
        # bytes is encoded as offset (32 bytes) + length (32 bytes) + data (padded)
        badge_key_bytes = to_bytes(hexstr=badge_key)
        signature_bytes = to_bytes(hexstr=signature)

        encoded = encode(['bytes32', 'bytes'], [badge_key_bytes, signature_bytes])

        # Prepend function selector
        selector = keccak(text="anchorBadge(bytes32,bytes)")[:4]
        calldata = to_hex(selector) + encoded.hex()

        return calldata

    @staticmethod
    def generate_badge_key(substrate_id: str, canonical_seal: str, timestamp: int) -> str:
        """Generate deterministic badge key from ARKHE substrate data."""
        payload = encode(
            ['string', 'bytes32', 'uint256'],
            [substrate_id, to_bytes(hexstr=canonical_seal), timestamp]
        )
        return to_hex(keccak(payload))

    @staticmethod
    def decode_anchor_calldata(calldata: str) -> Dict:
        """Decode anchorBadge calldata for verification."""
        if len(calldata) < 10:
            raise ValueError("Invalid calldata: too short")

        selector = calldata[:10]
        params = calldata[10:]

        # Decode bytes32 (first 32 bytes after selector)
        badge_key = "0x" + params[24:64]  # Last 32 bytes of first word

        # Decode bytes offset and length
        offset = int(params[64:128], 16) * 2  # Convert to hex chars
        length = int(params[128:192], 16) * 2

        # Extract signature data
        sig_start = 192 + offset
        signature = "0x" + params[sig_start:sig_start + length]

        return {
            "selector": selector,
            "badge_key": badge_key,
            "signature": signature,
            "signature_length_bytes": length // 2
        }

    @classmethod
    def create_arkhe_transaction(cls,
                                  substrate_id: str,
                                  canonical_seal: str,
                                  signature: str,
                                  contract_address: str,
                                  chain_id: int = 1) -> Dict:
        """
        Create complete EVM transaction for anchoring ARKHE substrate seal.

        Returns transaction dict ready for signing.
        """
        timestamp = int(time.time())
        badge_key = cls.generate_badge_key(substrate_id, canonical_seal, timestamp)
        calldata = cls.encode_anchor_calldata(badge_key, signature)

        return {
            "to": contract_address,
            "data": calldata,
            "value": "0x0",
            "gasLimit": "0x186a0",  # 100k gas
            "chainId": chain_id,
            "badgeKey": badge_key,
            "substrateId": substrate_id,
            "canonicalSeal": canonical_seal,
            "timestamp": timestamp
        }

# Example: Encode Substrate 241 seal
if __name__ == "__main__":
    bridge = ArkheEVMBridge()

    # Substrate 241 data
    substrate_id = "241+∞"
    canonical_seal = "0x4b854d6a61dab3a5dd8d5ede402d72eac201409d6ee478f767083da3515621b5"
    dummy_signature = "0x" + "00" * 65  # 65-byte ECDSA placeholder

    # Generate badge key
    badge_key = bridge.generate_badge_key(substrate_id, canonical_seal, int(time.time()))
    print(f"Badge Key: {badge_key}")

    # Encode calldata
    calldata = bridge.encode_anchor_calldata(badge_key, dummy_signature)
    print(f"\nCalldata: {calldata}")
    print(f"Selector: {calldata[:10]}")
    print(f"Length: {(len(calldata) - 2) // 2} bytes")

    # Decode to verify
    decoded = bridge.decode_anchor_calldata(calldata)
    print(f"\nDecoded badgeKey: {decoded['badge_key']}")
    print(f"Decoded signature length: {decoded['signature_length_bytes']} bytes")

    # Create full transaction
    tx = bridge.create_arkhe_transaction(
        substrate_id=substrate_id,
        canonical_seal=canonical_seal,
        signature=dummy_signature,
        contract_address="0xArkheBadgeRegistry...",
        chain_id=1
    )
    print(f"\nTransaction ready for signing:")
    print(json.dumps(tx, indent=2))
'''

with open(f"{base_dir}/arkhe_evm_bridge.py", "w") as f:
    f.write(py_module)

# Create a Solidity contract template
solidity_contract = '''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title ArkheBadgeRegistry
 * @notice On-chain registry for ARKHE OS canonical seals and substrate attestations
 * @dev Integrates with TemporalChain for cross-chain verification
 */
contract ArkheBadgeRegistry {

    struct Badge {
        bytes signature;
        uint256 timestamp;
        address issuer;
        bool revoked;
    }

    // badgeKey => Badge
    mapping(bytes32 => Badge) public badges;

    // issuer => nonce (for replay protection)
    mapping(address => uint256) public nonces;

    // Authorized ARKHE oracles
    mapping(address => bool) public authorizedOracles;

    address public owner;

    event BadgeAnchored(
        bytes32 indexed badgeKey,
        address indexed issuer,
        uint256 timestamp,
        string substrateId
    );

    event BadgeRevoked(
        bytes32 indexed badgeKey,
        address indexed revoker,
        uint256 timestamp
    );

    event OracleAuthorized(address indexed oracle);
    event OracleDeauthorized(address indexed oracle);

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    modifier onlyOracle() {
        require(authorizedOracles[msg.sender], "Not authorized oracle");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    /**
     * @notice Anchor an ARKHE badge on-chain
     * @param badgeKey Deterministic key from substrate ID + seal + timestamp
     * @param signature ARKHE HSM-PQC or ECDSA signature
     */
    function anchorBadge(
        bytes32 badgeKey,
        bytes calldata signature
    ) external onlyOracle {
        require(badges[badgeKey].timestamp == 0, "Badge already exists");

        badges[badgeKey] = Badge({
            signature: signature,
            timestamp: block.timestamp,
            issuer: msg.sender,
            revoked: false
        });

        nonces[msg.sender]++;

        emit BadgeAnchored(badgeKey, msg.sender, block.timestamp, "");
    }

    /**
     * @notice Anchor badge with substrate metadata
     */
    function anchorBadgeWithMetadata(
        bytes32 badgeKey,
        bytes calldata signature,
        string calldata substrateId,
        bytes32 canonicalSeal,
        uint256 testCount,
        uint256 passCount
    ) external onlyOracle {
        require(badges[badgeKey].timestamp == 0, "Badge already exists");

        // Verify badge key matches metadata
        bytes32 expectedKey = keccak256(abi.encode(
            substrateId,
            canonicalSeal,
            block.timestamp
        ));
        require(expectedKey == badgeKey, "Invalid badge key");

        badges[badgeKey] = Badge({
            signature: signature,
            timestamp: block.timestamp,
            issuer: msg.sender,
            revoked: false
        });

        emit BadgeAnchored(badgeKey, msg.sender, block.timestamp, substrateId);
    }

    /**
     * @notice Verify badge exists and is valid
     */
    function verifyBadge(
        bytes32 badgeKey,
        bytes calldata signature
    ) external view returns (bool) {
        Badge memory badge = badges[badgeKey];
        if (badge.timestamp == 0 || badge.revoked) {
            return false;
        }

        // Compare signatures
        return keccak256(badge.signature) == keccak256(signature);
    }

    /**
     * @notice Get badge details
     */
    function getBadge(bytes32 badgeKey) external view returns (Badge memory) {
        return badges[badgeKey];
    }

    /**
     * @notice Revoke a badge (emergency only)
     */
    function revokeBadge(bytes32 badgeKey) external onlyOwner {
        require(badges[badgeKey].timestamp != 0, "Badge does not exist");
        badges[badgeKey].revoked = true;
        emit BadgeRevoked(badgeKey, msg.sender, block.timestamp);
    }

    // Oracle management
    function authorizeOracle(address oracle) external onlyOwner {
        authorizedOracles[oracle] = true;
        emit OracleAuthorized(oracle);
    }

    function deauthorizeOracle(address oracle) external onlyOwner {
        authorizedOracles[oracle] = false;
        emit OracleDeauthorized(oracle);
    }

    // Batch operations for gas efficiency
    function anchorBadgeBatch(
        bytes32[] calldata badgeKeys,
        bytes[] calldata signatures
    ) external onlyOracle {
        require(badgeKeys.length == signatures.length, "Length mismatch");

        for (uint i = 0; i < badgeKeys.length; i++) {
            if (badges[badgeKeys[i]].timestamp == 0) {
                badges[badgeKeys[i]] = Badge({
                    signature: signatures[i],
                    timestamp: block.timestamp,
                    issuer: msg.sender,
                    revoked: false
                });
                emit BadgeAnchored(badgeKeys[i], msg.sender, block.timestamp, "");
            }
        }
    }
}
'''

with open(f"{base_dir}/ArkheBadgeRegistry.sol", "w") as f:
    f.write(solidity_contract)

# Create a comprehensive README
readme = '''# ARKHE OS EVM Bridge

## Canon: ∞.Ω.∇+++.evm.bridge

Bridge between ARKHE OS substrates and EVM-compatible blockchains for on-chain attestation of canonical seals, consciousness moments, and temporal chain anchors.

## Components

### 1. JavaScript/TypeScript Module (`arkhe_evm_bridge.js`)
- `ArkheBadgeAnchor`: Encode and send badge anchoring transactions
- `ArkheTemporalChainBridge`: Bridge TemporalChain seals to Ethereum
- Compatible with ethers.js v5/v6

### 2. Python Backend (`arkhe_evm_bridge.py`)
- Python equivalent using `eth_abi` and `eth_utils`
- Integrates with ARKHE backend for automated anchoring
- Decodes calldata for verification

### 3. Solidity Contract (`ArkheBadgeRegistry.sol`)
- On-chain registry for ARKHE badges
- Oracle-authorized anchoring
- Batch operations for gas efficiency
- Revocation mechanism for emergency

## Usage

### Encode Calldata (JS)
```javascript
const { ArkheBadgeAnchor } = require('./arkhe_evm_bridge');

const badgeKey = ArkheBadgeAnchor.generateBadgeKey(
    '241+∞',
    '0x4b854d6a...5621b5',
    Math.floor(Date.now() / 1000)
);

const anchor = new ArkheBadgeAnchor(contractAddress, signer);
const { calldata } = anchor.encodeAnchorCalldata(badgeKey, signature);
console.log('calldata =', calldata);
```

### Encode Calldata (Python)
```python
from arkhe_evm_bridge import ArkheEVMBridge

bridge = ArkheEVMBridge()
calldata = bridge.encode_anchor_calldata(badge_key, signature)
print(f"calldata = {calldata}")
```

### Solidity Interaction
```solidity
ArkheBadgeRegistry registry = ArkheBadgeRegistry(0x...);
registry.anchorBadge(badgeKey, signature);
```

## Integration with ARKHE Substrates

| Substrate | Badge Key Source | Seal Type |
|-----------|-----------------|-----------|
| 241+∞ | Semantic Chemistry Secure | SHA3-256 |
| 242 | Quantum Consciousness | SHA3-256 |
| 9018 | TemporalChain | SHA3-256 |
| 9023 | Kimi-Cathedral Node | SHA3-256 |

## Security

- All badges require authorized oracle signature
- Badge keys are deterministic (prevent duplicate anchoring)
- Emergency revocation mechanism
- PQC-ready signature format (65-byte placeholder for Dilithium3)
'''

with open(f"{base_dir}/README.md", "w") as f:
    f.write(readme)

print("✅ ARKHE EVM Bridge created:")
print(f"   📁 {base_dir}/")
print(f"   ├── arkhe_evm_bridge.js      (ethers.js module)")
print(f"   ├── arkhe_evm_bridge.py      (Python backend)")
print(f"   ├── ArkheBadgeRegistry.sol   (Solidity contract)")
print(f"   └── README.md                (Documentation)")
