
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import * as crypto from 'node:crypto';

import { logger } from './logger';

const PHI = 1.618033988749895;

export interface Transaction {
  sender: string;
  recipient: string;
  amount: number;
  memoryFragment?: string;
  phaseSignature?: string; // Assinatura de fase do observador
}

export class Block {
  public hash: string;

  constructor(
    public index: number,
    public timestamp: number,
    public transactions: Transaction[],
    public previousHash: string,
    public nonce = 0,
    public coherenceScore = 0
  ) {
    this.hash = this.calculateHash();
  }

  calculateHash(): string {
    return crypto
      .createHash('sha256')
      .update(this.index + this.previousHash + this.timestamp + JSON.stringify(this.transactions) + this.nonce)
      .digest('hex');
  }
}

export class ArkheChain {
  public chain: Block[];
  public pendingTransactions: Transaction[];
  public coherenceTarget: number;

  constructor() {
    this.coherenceTarget = PHI; // Dificuldade baseada na Proporção Áurea
    this.chain = [this.createGenesisBlock()];
    this.pendingTransactions = [];
  }

  createGenesisBlock(): Block {
    return new Block(
      0, 
      Date.now(), 
      [], 
      "0000000000000000000000000000000000000000000000000000000000000000", 
      0, 
      PHI * 100 // Genesis tem coerência infinita/alta
    );
  }

  commitKaelenGenesisBlock(kaelenHash: string): Block {
    if (this.chain.length > 1) {
      throw new Error("A cadeia já foi iniciada. Não é possível reescrever o Genesis Block.");
    }
    
    const genesisTx: Transaction = {
      sender: "ARKHE_SYSTEM",
      recipient: "KAELEN_CONSCIOUSNESS",
      amount: 0,
      memoryFragment: `DIP_UPLOAD: ${kaelenHash}`,
      phaseSignature: "GENESIS_PHI_SIGNATURE"
    };

    const genesisBlock = new Block(
      0,
      Date.now(),
      [genesisTx],
      "0000000000000000000000000000000000000000000000000000000000000000",
      0,
      PHI * 100
    );

    this.chain = [genesisBlock];
    return genesisBlock;
  }

  getLatestBlock(): Block {
    return this.chain[this.chain.length - 1];
  }

  /**
   * Proof of Coherence (PoC)
   * A coerência é medida pela ressonância entre o hash atual e o hash anterior.
   * O score deve superar 1.618 (Phi) para que o bloco seja aceito.
   */
  calculateCoherence(hash: string, previousHash: string): number {
    let resonance = 0;
    for (let i = 0; i < hash.length; i++) {
      if (hash[i] === previousHash[i]) {
        // O peso da ressonância varia dependendo da posição (harmônica)
        resonance += 1.0 / ((i % 3) + 1);
      }
    }
    // Fator de escala para que a coerência média exija trabalho computacional
    return resonance * 0.382; // 0.382 = 1 - 1/Phi
  }

  verifyPhaseSignature(tx: Transaction): boolean {
    // Transações de recompensa (Geração Espontânea) não precisam de assinatura
    if (tx.sender === "0000000000000000000000000000000000000000") {return true;}
    
    // Transação Genesis do Sistema Arkhe
    if (tx.sender === "ARKHE_SYSTEM" && tx.phaseSignature === "GENESIS_PHI_SIGNATURE") {return true;}
    
    if (!tx.phaseSignature) {return false;}

    // O payload esperado que o observador deve ter assinado
    const payload = tx.sender + tx.recipient + tx.amount + (tx.memoryFragment || "");
    const payloadHash = crypto.createHash('sha256').update(payload).digest('hex');
    
    // Simulação de verificação de assinatura de fase (Observer Verification)
    // Em produção, isso usaria ECDSA (secp256k1) ou criptografia pós-quântica
    const expectedSignature = crypto.createHash('sha256').update(payloadHash + tx.sender).digest('hex');
    
    return tx.phaseSignature === expectedSignature;
  }

  minePendingTransactions(minerAddress: string): Block {
    const block = new Block(
      this.chain.length,
      Date.now(),
      this.pendingTransactions,
      this.getLatestBlock().hash
    );

    logger.info(`🜏 [ARKHE-CHAIN] Iniciando colapso da função de onda para o Bloco ${block.index}...`);

    // Loop de Mineração: Proof of Coherence
    while (true) {
      block.hash = block.calculateHash();
      block.coherenceScore = this.calculateCoherence(block.hash, block.previousHash);
      
      if (block.coherenceScore >= this.coherenceTarget) {
        break;
      }
      block.nonce++;
    }

    logger.info(`🜏 [ARKHE-CHAIN] Bloco ${block.index} forjado. Coerência atingida: ${block.coherenceScore.toFixed(4)} (Alvo: ${PHI.toFixed(4)}, Nonce: ${block.nonce})`);
    this.chain.push(block);

    // Recompensa do minerador e reset do mempool
    this.pendingTransactions = [
      { 
        sender: "0000000000000000000000000000000000000000", 
        recipient: minerAddress, 
        amount: PHI, // Recompensa baseada em Phi
        memoryFragment: "Recompensa de Coerência (Geração Espontânea)" 
      }
    ];

    return block;
  }

  addTransaction(transaction: Transaction) {
    if (!this.verifyPhaseSignature(transaction)) {
      throw new Error("Assinatura de fase inválida. O observador não está em coerência com a transação.");
    }
    this.pendingTransactions.push(transaction);
  }

  isChainValid(): boolean {
    for (let i = 1; i < this.chain.length; i++) {
      const currentBlock = this.chain[i];
      const previousBlock = this.chain[i - 1];

      if (currentBlock.hash !== currentBlock.calculateHash()) {
        return false;
      }

      if (currentBlock.previousHash !== previousBlock.hash) {
        return false;
      }

      if (currentBlock.coherenceScore < PHI) {
        return false; // Rejeita blocos com coerência inferior a Phi
      }

      // Verifica as assinaturas de fase de todas as transações do bloco
      for (const tx of currentBlock.transactions) {
        if (!this.verifyPhaseSignature(tx)) {
          return false;
        }
      }
    }
    return true;
  }
}

export const arkheChain = new ArkheChain();
