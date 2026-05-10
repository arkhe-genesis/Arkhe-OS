// ============================================================================
// ARKHE Ω-TEMP — Temporal Hash Chain (WebRTC Peer)
// ============================================================================
// Cada nó WebRTC mantém sua própria cadeia temporal.
// A sincronização entre nós é feita via Merkle tree exchange.
// ============================================================================

import { TemporalBlock, TemporalMessage, Address } from './types';
import { keccak256Sync } from '../crypto/keccak';

export class TemporalHashChain {
  private blocks: TemporalBlock[] = [];
  private hashIndex: Map<string, number> = new Map(); // blockHash → index
  private _stateRoot: Uint8Array;

  constructor() {
    this.blocks = [];
    this._stateRoot = keccak256Sync(new Uint8Array(0));
    this.createGenesisBlock();
  }

  // Cria bloco gênesis
  private createGenesisBlock(): void {
    const genesisPayload = new TextEncoder().encode('ARKHE_GENESIS_Ω-TEMP_v4.3.9');
    const stateRoot = keccak256Sync(genesisPayload);

    const genesis: TemporalBlock = {
      index: 0,
      prevHash: new Uint8Array(32),
      timestamp: Date.now() * 1_000_000, // nanossegundos
      messages: [{
        id: 'genesis',
        sender: '0x00000000000000000000',
        receiver: '0x00000000000000000000',
        sourceTs: 0,
        targetTs: Infinity,
        content: 'GENESIS_BLOCK',
        payload: new Uint8Array(),
      }],
      stateRoot: stateRoot,
      oracleRoot: new Uint8Array(32),
      validatorSig: new Uint8Array(),
    };

    genesis.prevHash = new Uint8Array(32); // Zeros para genesis
    this.blocks.push(genesis);
    this.hashIndex.set(this.bytesToHex(this.blockHash(genesis)), 0);
    this._stateRoot = stateRoot;
  }

  // Adiciona novo bloco
  appendBlock(messages: TemporalMessage[], prevHash?: Uint8Array): TemporalBlock | null {
    const prevBlock = this.blocks[this.blocks.length - 1];
    const actualPrevHash = prevHash || this.blockHash(prevBlock);

    const index = this.blocks.length;
    const timestamp = BigInt(Date.now()) * 1_000_000n;

    // Ordenar mensagens por sourceTs para consistência determinística
    const sorted = [...messages].sort((a, b) => a.sourceTs - b.sourceTs);

    // Calcular Merkle root das mensagens
    const msgHashes = sorted.map(m => keccak256Sync(
      new TextEncoder().encode(`${m.id}:${m.sender}:${m.receiver}:${m.sourceTs}`)
    ));
    const stateRoot = this.merkleRoot(msgHashes);

    // Calcular oracle root (simplificado)
    const oracleScores = sorted.map(m => m.consistencyScore ?? 0.5);
    const oracleRoot = keccak256Sync(
      new Uint8Array(Float64Array.from(oracleScores).buffer)
    );

    const block: TemporalBlock = {
      index,
      prevHash: actualPrevHash,
      timestamp: Number(timestamp),
      messages: sorted,
      stateRoot,
      oracleRoot,
      validatorSig: new Uint8Array(),
    };

    this.blocks.push(block);
    const hash = this.blockHash(block);
    this.hashIndex.set(this.bytesToHex(hash), index);
    this._stateRoot = stateRoot;

    return block;
  }

  // Calcula hash de um bloco
  blockHash(block: TemporalBlock): Uint8Array {
    const header = new Uint8Array(128);
    const view = new DataView(header.buffer);

    view.setUint32(0, block.index, false);
    header.set(block.prevHash, 8);
    view.setBigUint64(40, BigInt(block.timestamp), false);
    header.set(block.stateRoot, 48);
    header.set(block.oracleRoot, 80);
    view.setUint32(112, block.messages.length, false);

    return keccak256Sync(header);
  }

  // Valida integridade da cadeia
  validateChain(): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

    for (let i = 1; i < this.blocks.length; i++) {
      const current = this.blocks[i];
      const previous = this.blocks[i - 1];

      // Verificar prevHash
      const expectedPrev = this.blockHash(previous);
      if (!this.equals(current.prevHash, expectedPrev)) {
        errors.push(`Bloco ${i}: prevHash inválido`);
      }

      // Verificar timestamp
      if (current.timestamp <= previous.timestamp) {
        errors.push(`Bloco ${i}: timestamp não-causal`);
      }

      // Verificar Merkle root
      const msgHashes = current.messages.map(m => keccak256Sync(
        new TextEncoder().encode(`${m.id}:${m.sender}:${m.receiver}:${m.sourceTs}`)
      ));
      const computedRoot = this.merkleRoot(msgHashes);
      if (!this.equals(current.stateRoot, computedRoot)) {
        errors.push(`Bloco ${i}: Merkle root inválido`);
      }
    }

    return { valid: errors.length === 0, errors };
  }

  // Retorna índice de um bloco por hash
  getBlockIndex(hash: Uint8Array): number | undefined {
    return this.hashIndex.get(this.bytesToHex(hash));
  }

  // Retorna bloco por índice
  getBlock(index: number): TemporalBlock | undefined {
    return this.blocks[index];
  }

  // Último bloco
  get lastBlock(): TemporalBlock {
    return this.blocks[this.blocks.length - 1];
  }

  // Comprimento da cadeia
  get length(): number {
    return this.blocks.length;
  }

  // State root atual
  get stateRoot(): Uint8Array {
    return this._stateRoot;
  }

  // Itera blocos (generator)
  *[Symbol.iterator](): Generator<TemporalBlock> {
    for (const block of this.blocks) {
      yield block;
    }
  }

  // Merkle root computation
  private merkleRoot(hashes: Uint8Array[]): Uint8Array {
    if (hashes.length === 0) return keccak256Sync(new Uint8Array(0));
    if (hashes.length === 1) return hashes[0];

    let level = hashes;
    while (level.length > 1) {
      const next: Uint8Array[] = [];
      for (let i = 0; i < level.length; i += 2) {
        if (i + 1 < level.length) {
          next.push(keccak256Sync(new Uint8Array([
            ...level[i], ...level[i + 1]
          ])));
        } else {
          next.push(keccak256Sync(new Uint8Array([
            ...level[i], ...level[i]
          ])));
        }
      }
      level = next;
    }
    return level[0];
  }

  private equals(a: Uint8Array, b: Uint8Array): boolean {
    if (a.length !== b.length) return false;
    for (let i = 0; i < a.length; i++) {
      if (a[i] !== b[i]) return false;
    }
    return true;
  }

  private bytesToHex(bytes: Uint8Array): string {
    return Array.from(bytes).map(b => b.toString(16).padStart(2, '0')).join('');
  }
}
