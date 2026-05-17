# ARKHE OS EVM Bridge

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
