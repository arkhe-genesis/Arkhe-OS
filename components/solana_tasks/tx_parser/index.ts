import { Connection, PublicKey, TransactionResponse } from '@solana/web3.js';
import * as borsh from 'borsh';

// Example Borsh Schema (Mock)
class CounterState {
    count: number;
    bump: number;

    constructor(fields: { count: number, bump: number } | undefined = undefined) {
        if (fields) {
            this.count = fields.count;
            this.bump = fields.bump;
        } else {
            this.count = 0;
            this.bump = 0;
        }
    }
}

const CounterSchema = new Map([
    [CounterState, { kind: 'struct', fields: [['count', 'u64'], ['bump', 'u8']] }]
]);

async function parseTransaction(txSignature: string, rpcUrl: string) {
    const connection = new Connection(rpcUrl, 'confirmed');
    const tx: TransactionResponse | null = await connection.getTransaction(txSignature, {
        maxSupportedTransactionVersion: 0
    });

    if (!tx) {
        console.error("Transaction not found.");
        return;
    }

    console.log(`Transaction Signature: ${txSignature}`);
    console.log(`Block Time: ${tx.blockTime}`);

    // In a real scenario, you would inspect instructions or account data
    // Here we mock reading some returned buffer (e.g. from an account or return data)

    // Mock Buffer for a CounterState (count: 42, bump: 255)
    // 8 bytes for u64 (42), 1 byte for u8 (255)
    const mockBuffer = Buffer.from([42, 0, 0, 0, 0, 0, 0, 0, 255]);

    try {
        const decoded = borsh.deserialize(
            CounterSchema,
            CounterState,
            mockBuffer
        );
        console.log("Decoded Borsh Data:");
        console.log(decoded);
    } catch (e) {
        console.error("Failed to decode data", e);
    }
}

const args = process.argv.slice(2);
if (args.length >= 2) {
    parseTransaction(args[0], args[1]);
} else {
    console.log("Usage: ts-node index.ts <tx_signature> <rpc_url>");
}
