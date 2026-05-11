// ============================================================================
// ARKHE Ω-TEMP — Peer-to-Peer Protocol over WebRTC
// ============================================================================

import {
  ArkheFrame, ArkheFrameHeader, ArkheFrameType, TemporalMessage,
  Address, RouteResult
} from '../core/types';
import { ARKHE_MAGIC_BYTES } from '../config/arkhe';

const PROTOCOL_VERSION = 0x0439; // 4.3.9

export class ArkheProtocol {
  static createFrame(type: ArkheFrameType, payload: Uint8Array, seqNum?: number): ArkheFrame {
    return {
      header: {
        magic: ARKHE_MAGIC_BYTES,
        version: PROTOCOL_VERSION,
        type,
        seqNum: seqNum ?? Math.floor(Math.random() * 0xFFFFFFFF),
        payloadLen: payload.length,
      },
      payload,
    };
  }

  static serializeFrame(frame: ArkheFrame): Uint8Array {
    const totalSize = 16 + frame.payload.length;
    const buffer = new Uint8Array(totalSize);
    const view = new DataView(buffer.buffer);
    buffer.set(frame.header.magic, 0);
    view.setUint16(4, frame.header.version, false);
    buffer[6] = frame.header.type;
    buffer[7] = 0;
    view.setUint32(8, frame.header.seqNum, false);
    view.setUint32(12, frame.header.payloadLen, false);
    buffer.set(frame.payload, 16);
    return buffer;
  }

  static deserializeFrame(data: Uint8Array): ArkheFrame | null {
    if (data.length < 16) return null;
    for (let i = 0; i < 4; i++) if (data[i] !== ARKHE_MAGIC_BYTES[i]) return null;
    const view = new DataView(data.buffer);
    const header: ArkheFrameHeader = {
      magic: data.slice(0, 4),
      version: view.getUint16(4, false),
      type: data[6] as ArkheFrameType,
      seqNum: view.getUint32(8, false),
      payloadLen: view.getUint32(12, false),
    };
    if (16 + header.payloadLen > data.length) return null;
    return { header, payload: data.slice(16, 16 + header.payloadLen) };
  }

  // Mensagem temporal
  static createTemporalMessage(msg: TemporalMessage): ArkheFrame {
    return this.createFrame(ArkheFrameType.TEMPORAL_MESSAGE, new TextEncoder().encode(JSON.stringify(msg)));
  }
  static parseTemporalMessage(frame: ArkheFrame): TemporalMessage {
    return JSON.parse(new TextDecoder().decode(frame.payload));
  }

  // Block
  static createBlockAnnounce(block: any): ArkheFrame {
    const json = JSON.stringify(block);
    const payload = new TextEncoder().encode(json);
    return this.createFrame(ArkheFrameType.BLOCK_ANNOUNCE, payload);
  }
  static parseBlockAnnounce(frame: ArkheFrame): any {
    return JSON.parse(new TextDecoder().decode(frame.payload));
  }

  // Route Request
  static createRouteRequest(requestId: number, destination: Address, maxHops: number = 16): ArkheFrame {
    const destBytes = hexToBytes(destination);
    const payload = new Uint8Array(4 + destBytes.length + 2);
    const view = new DataView(payload.buffer);
    view.setUint32(0, requestId, false);
    payload.set(destBytes, 4);
    view.setUint16(4 + destBytes.length, maxHops, false);
    return this.createFrame(ArkheFrameType.ROUTE_REQUEST, payload);
  }
  static parseRouteRequest(frame: ArkheFrame): { requestId: number; destination: Address; maxHops: number } {
    const view = new DataView(frame.payload.buffer);
    return { requestId: view.getUint32(0, false), destination: bytesToHex(frame.payload.slice(4, 24)), maxHops: view.getUint16(24, false) };
  }

  // Route Response
  static createRouteResponse(requestId: number, route: RouteResult): ArkheFrame {
    const pathBytesList = route.path.map(p => Array.from(hexToBytes(p)));
    const pathBytes = new Uint8Array(pathBytesList.flat());
    const payload = new Uint8Array(4 + 4 + 8 + 8 + 4 + pathBytes.length);
    const view = new DataView(payload.buffer);
    let offset = 0;
    view.setUint32(offset, requestId, false); offset += 4;
    view.setUint32(offset, route.hops, false); offset += 4;
    view.setFloat64(offset, route.totalCost, false); offset += 8;
    view.setFloat64(offset, route.minConsensus, false); offset += 8;
    view.setUint32(offset, route.path.length, false); offset += 4;
    payload.set(pathBytes, offset);
    return this.createFrame(ArkheFrameType.ROUTE_RESPONSE, payload);
  }

  // Ping/Pong
  static createPing(): ArkheFrame {
    const payload = new Uint8Array(8);
    new DataView(payload.buffer).setBigUint64(0, BigInt(Math.floor(performance.timeOrigin + performance.now())), false);
    return this.createFrame(ArkheFrameType.PING, payload);
  }
  static createPong(pingSeq: number): ArkheFrame {
    const payload = new Uint8Array(8);
    new DataView(payload.buffer).setUint32(0, pingSeq, false);
    return this.createFrame(ArkheFrameType.PONG, payload);
  }

  // Merkle
  static createMerkleRequest(leafIndex: number): ArkheFrame {
    const payload = new Uint8Array(4);
    new DataView(payload.buffer).setUint32(0, leafIndex, false);
    return this.createFrame(ArkheFrameType.MERKLE_REQUEST, payload);
  }
  static createMerkleProof(proof: any): ArkheFrame {
    return this.createFrame(ArkheFrameType.MERKLE_PROOF, new TextEncoder().encode(JSON.stringify(proof)));
  }

  static parseMerkleProof(frame: ArkheFrame): any {
    return JSON.parse(new TextDecoder().decode(frame.payload));
  }

  // Consensus
  static createConsensusProposal(blockIndex: number, blockHash: Uint8Array, validator: Address, signature: Uint8Array): ArkheFrame {
    const payload = new Uint8Array(4 + 32 + 20 + signature.length);
    const view = new DataView(payload.buffer);
    view.setUint32(0, blockIndex, false);
    payload.set(blockHash, 4);
    payload.set(hexToBytes(validator), 36);
    payload.set(signature, 56);
    return this.createFrame(ArkheFrameType.CONSENSUS_PROPOSAL, payload);
  }

  static createConsensusVote(vote: { blockIndex: number; approve: boolean; signature: Uint8Array }): ArkheFrame {
    const payload = new Uint8Array(4 + 1 + 64);
    const view = new DataView(payload.buffer);
    view.setUint32(0, vote.blockIndex, false);
    payload[4] = vote.approve ? 1 : 0;
    payload.set(vote.signature, 5);
    return this.createFrame(ArkheFrameType.CONSENSUS_VOTE, payload);
  }
}

function hexToBytes(hex: string): Uint8Array {
  const clean = hex.replace(/^0x/, '').padStart(40, '0');
  const bytes = new Uint8Array(20);
  for (let i = 0; i < 40; i += 2) bytes[i / 2] = parseInt(clean.slice(i, i + 2), 16);
  return bytes;
}

function bytesToHex(bytes: Uint8Array): string {
  return '0x' + Array.from(bytes).map(b => b.toString(16).padStart(2, '0')).join('');
}
