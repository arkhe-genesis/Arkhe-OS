
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ArkheChainCore } from '../src';

describe('ArkheChainCore', () => {
  it('should calculate hash correctly', () => {
    const block = {
      index: 0,
      timestamp: 123456789,
      transactions: [],
      previousHash: '0000',
      nonce: 0,
      coherenceScore: 1.618,
    };
    const hash = ArkheChainCore.calculateHash(block);
    expect(hash).toBeDefined();
    expect(hash.length).toBe(64);
  });

  it('should calculate coherence correctly', () => {
    const hash1 = 'abc123456789';
    const hash2 = 'abc987654321';
    const coherence = ArkheChainCore.calculateCoherence(hash1, hash2);
    expect(coherence).toBeGreaterThan(0);
  });

  it('should verify genesis phase signature', () => {
    const tx = {
      sender: 'ARKHE_SYSTEM',
      recipient: 'KAELEN_CONSCIOUSNESS',
      amount: 10,
      phaseSignature: 'GENESIS_PHI_SIGNATURE',
    };
    expect(ArkheChainCore.verifyPhaseSignature(tx)).toBe(true);
  });
});
