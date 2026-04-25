
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

/**
 * 🜏 Tzinor Memory State (Evolutionary State)
 * Mapeamento: Cortex (Software) + Ma & Patterson (Hardware) + Whittaker (Física)
 */

export interface ContextNode {
  /** Tempo de origem da informação (Onda Avançada) */
  timestamp?: number;
  /** Representação vetorial no espaço latente */
  embedding: number[];
  /** Relevância atual (sujeita ao decaimento de Warp) */
  salience: number;
}

export interface MemoryEngram {
  /** Tempo em que a memória foi gerada */
  originTime: number;
  /** Tempo em que o contexto esfriou e foi consolidado no HBF */
  consolidatedTime: number;
  /** Hash do sumário gerado por reflexão do LLM */
  summaryHash: string;
  /** Peso de ressonância (importância histórica) */
  resonanceWeight: number;
}

export interface TzinorMemoryState {
  /** Identificador único do Bio-Nó na Teknet */
  agentId: string;
  
  /** Época atual da Timechain */
  currentEpoch: number;
  
  /** 
   * Potencial F (Contexto Imediato / Onda Avançada)
   * A janela de atenção ativa (KV Cache / PNM)
   * "O que importa agora"
   */
  fContext: ContextNode[];
  
  /** 
   * Potencial G (Memória Histórica / Onda Retardada)
   * O reservatório persistente de interações passadas (HBF)
   * "Por que importa"
   */
  gMemory: MemoryEngram[];
  
  /** 
   * Fator de Warp (Decaimento de Randall-Sundrum)
   * W = e^{-k Δt}
   */
  warpFactor: number;
  
  /** Coerência λ₂ do Estado Evolutivo */
  lambdaCoherence: number;
}
