# 🔐 ARKHE-ETHEREUM SECURITY AUDIT & P1-P7 MAPPING

## Pre-Audit Checklist (Slither / Solhint)
- [x] Run `slither .` on all Solidity contracts.
- [x] Run `solhint 'contracts/**/*.sol'`.
- [x] Ensure Solidity version is locked to `0.8.19` (avoid `^` in production).
- [x] Verify use of Custom Errors over Revert Strings to save gas.
- [x] Check Reentrancy vulnerabilities (e.g. `settlePayment` uses CEI pattern).
- [x] Validate access control modifiers (e.g. `onlyRegistered`).

## P1-P7 Constitutional Mapping

| Control Level | Component | Audit Validation |
|---------------|-----------|------------------|
| **P1 - Substrate Identity** | `ArkheIdentity.sol` | Verify ORCID to Address bi-directional binding is immutable and non-spoofable. |
| **P2 - TemporalChain Continuity** | `ArkheTokenBridge.sol` | Ensure `anchorSeal` correctly logs the block timestamp and prevents duplicate seal hashes. |
| **P3 - Phi_C Impact** | `ArkheTokenBridge.sol` | Validate the integrity of `phiCScore` metadata when anchoring. |
| **P4 - PQC Signature** | `ArkheIdentity.sol` | Ensure `pqcPublicKey` allows sufficient byte length for ML-DSA-65 keys. |
| **P5 - Economic Protocol (x402)** | `ArkhePaymentGateway.sol` | Ensure `requestPayment` and `settlePayment` maintain strict accounting and prevent double spends. |
| **P6 - Governance Federation** | `ArkheGovernance.sol` | Verify voting weight correctly factors reputation and correctly counts votes. |
| **P7 - ASI Sovereignty** | `arkhe_ethereum_bridge.py` | Ensure Python oracle acts securely, using correct RPC and private key management. |

## Actions for Formal Verification
1. Convert key state assertions in Solidity into formal specifications (e.g., using Certora or Halmos).
2. Create state machines mapping expected states for `ArkhePaymentGateway`.
3. Verify that `ArkheGovernance` vote counting cannot overflow or underflow under extreme conditions.
