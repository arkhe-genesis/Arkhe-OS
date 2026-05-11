// ============================================================================
// ARKHE Ω-TEMP — Tipos Fundamentais (WebRTC)
// ============================================================================

export type Address = string; // Hex string de 40 chars (160-bit)

export interface Timestamp {
  sourceTs: number;    // nanossegundos desde epoch
  targetTs: number;    // nanossegundos até expiração
}

// Mensagem temporal — unidade fundamental do protocolo
export interface TemporalMessage {
  id: string;
  sender: Address;
  receiver: Address;
  sourceTs: number;
  targetTs: number;
  content: string;
  payload: Uint8Array;
  consistencyScore?: number;  // [0, 1]
  zkProof?: Uint8Array;
  signature?: Uint8Array;
  metadata?: Record<string, string>;
}

// Bloco temporal
export interface TemporalBlock {
  index: number;
  prevHash: Uint8Array;
  timestamp: number;
  messages: TemporalMessage[];
  stateRoot: Uint8Array;
  oracleRoot: Uint8Array;
  validatorSig: Uint8Array;
}

// Informações do nó
export interface PeerInfo {
  address: Address;
  capabilities: string[];
  blockHeight: number;
  consistencyScore: number;
  latency: number;
  isRelayed: boolean;
}

// Resultado de roteamento
export interface RouteResult {
  path: Address[];
  totalCost: number;
  minConsensus: number;
  hops: number;
  estimatedLatency: number;
}

// Estado do consensus
export interface ConsensusState {
  chainLength: number;
  lastBlockHash: Uint8Array;
  totalConsistent: number;
  totalPruned: number;
  currentEpoch: number;
}

// Métricas do nó
export interface MeshMetrics {
  totalPeers: number;
  activePeers: number;
  relayedPeers: number;
  messagesSent: number;
  messagesReceived: number;
  avgLatencyMs: number;
  routingTableSize: number;
  chainLength: number;
  consensusScore: number;
}

// Frame type, imported from config
export { ArkheFrameType, ArkheFrame, ArkheFrameHeader } from '../config/arkhe';
