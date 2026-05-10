
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import * as crypto from 'node:crypto';

import pino from 'pino';
import { z } from 'zod';

// --- SHARED LOGGER ---
export const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  transport: {
    target: 'pino-pretty',
    options: {
      colorize: true,
    },
  },
});

// --- SCHEMAS ---
export const TransactionSchema = z.object({
  sender: z.string(),
  recipient: z.string(),
  amount: z.number().positive(),
  memoryFragment: z.string().optional(),
  phaseSignature: z.string().optional(),
});

export type Transaction = z.infer<typeof TransactionSchema>;

export const BlockSchema = z.object({
  index: z.number(),
  timestamp: z.number(),
  transactions: z.array(TransactionSchema),
  previousHash: z.string(),
  nonce: z.number(),
  coherenceScore: z.number(),
  hash: z.string(),
});

export type Block = z.infer<typeof BlockSchema>;

// --- BLOCKCHAIN LOGIC ---
const PHI = 1.618033988749895;

export class ArkheChainCore {
  public coherenceTarget: number = PHI;

  static calculateHash(block: Omit<Block, 'hash'>): string {
    return crypto
      .createHash('sha256')
      .update(block.index + block.previousHash + block.timestamp + JSON.stringify(block.transactions) + block.nonce)
      .digest('hex');
  }

  static calculateCoherence(hash: string, previousHash: string): number {
    let resonance = 0;
    for (let i = 0; i < Math.min(hash.length, previousHash.length); i++) {
      if (hash[i] === previousHash[i]) {
        resonance += 1.0 / ((i % 3) + 1);
      }
    }
    return resonance * 0.382;
  }

  static verifyPhaseSignature(tx: Transaction): boolean {
    if (tx.sender === "0000000000000000000000000000000000000000") {return true;}
    if (tx.sender === "ARKHE_SYSTEM" && tx.phaseSignature === "GENESIS_PHI_SIGNATURE") {return true;}
    if (!tx.phaseSignature) {return false;}

    const payload = tx.sender + tx.recipient + tx.amount + (tx.memoryFragment || "");
    const payloadHash = crypto.createHash('sha256').update(payload).digest('hex');
    const expectedSignature = crypto.createHash('sha256').update(payloadHash + tx.sender).digest('hex');

    return tx.phaseSignature === expectedSignature;
  }
}
