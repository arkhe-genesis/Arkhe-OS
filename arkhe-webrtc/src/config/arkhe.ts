// ============================================================================
// ARKHE Ω-TEMP — Configurações de Protocolo
// ============================================================================

export const ARKHE_PROTOCOL_VERSION = '4.3.9';
export const ARKHE_MAGIC_BYTES = new Uint8Array([0xCA, 0x72, 0x04, 0x39]); // "CA720439"

// Intervalo do bloco em milissegundos
export const BLOCK_INTERVAL_MS = 10_000; // 10 segundos

// Tamanhos máximos
export const MAX_MESSAGE_SIZE = 2048;           // bytes (por mensagem)
export const MAX_PAYLOAD_SIZE = 1024 * 1024;    // 1 MB
export const MAX_BLOCK_MESSAGES = 8192;         // mensagens por bloco
export const MAX_PEERS = 256;                   // máximo de peers simultâneos
export const MAX_HOP_COUNT = 16;                // máximo de hops na rede

// Thresholds de consenso (Q16.16 fixed-point)
export const CONSISTENCY_THRESHOLD = 0.85;
export const PARADOX_THRESHOLD = 0.95;

// WebRTC Data Channel configuração
export const DC_CONFIG: RTCDataChannelInit = {
  ordered: true,              // Mensagens devem chegar em ordem
  maxRetransmits: 3,          // Máximo tentativas de retransmissão
  negotiated: false,          // ID negociado via SDP
  id: undefined,              // Será atribuído dinamicamente
};

// Protocolo ARKHE sobre DataChannel
export const ARKHE_DC_LABEL = 'arkhe-v1';
export const ARKHE_DC_BINARY_TYPE = 'arraybuffer';

// Frame types (opcode)
export enum ArkheFrameType {
  // Mensagens básicas
  TEMPORAL_MESSAGE = 0x01,     // Mensagem temporal
  BLOCK_ANNOUNCE = 0x02,       // Anúncio de novo bloco
  BLOCK_REQUEST = 0x03,        // Requisição de bloco
  BLOCK_RESPONSE = 0x04,       // Resposta com bloco

  // Consenso
  CONSENSUS_VOTE = 0x10,       // Voto de consenso
  CONSENSUS_PROPOSAL = 0x11,   // Proposta de consenso
  CONSENSUS_COMMIT = 0x12,     // Commit de consenso

  // Roteamento
  ROUTE_REQUEST = 0x20,        // Requisição de rota
  ROUTE_RESPONSE = 0x21,       // Resposta de rota
  ROUTE_UPDATE = 0x22,         // Atualização de tabela de roteamento
  PING = 0x23,                 // Ping/Keep-alive
  PONG = 0x24,                 // Pong

  // Merkle sync
  MERKLE_REQUEST = 0x30,       // Requisição de prova Merkle
  MERKLE_PROOF = 0x31,         // Prova Merkle
  MERKLE_VERIFY = 0x32,        // Resultado de verificação

  // ZK Proofs
  ZK_PROOF_ANNOUNCE = 0x40,   // Anúncio de prova ZK
  ZK_PROOF_REQUEST = 0x41,    // Requisição de prova ZK
  ZK_PROOF_RESPONSE = 0x42,   // Resposta com prova ZK

  // Peer discovery
  PEER_HELLO = 0xF0,           // Hello handshake
  PEER_HELLO_ACK = 0xF1,       // Hello acknowledgment
  PEER_GOODBYE = 0xF2,         // Desconexão graciosa
  PEER_INFO = 0xF3,            // Informações do nó
}

// Header do frame ARKHE
export interface ArkheFrameHeader {
  magic: Uint8Array;           // 4 bytes - magic number
  version: number;             // 1 byte - versão do protocolo
  type: ArkheFrameType;        // 1 byte - tipo do frame
  seqNum: number;              // 4 bytes - número de sequência
  payloadLen: number;          // 4 bytes - comprimento do payload
}

// Estrutura de um frame ARKHE completo
export interface ArkheFrame {
  header: ArkheFrameHeader;
  payload: Uint8Array;
}
