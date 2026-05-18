/**
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
