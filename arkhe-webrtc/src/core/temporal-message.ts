// ============================================================================
// ARKHE Ω-TEMP — TemporalMessage (WebAssembly-compatible)
// ============================================================================
// Representação binária otimizada para serialização rápida sobre WebRTC.
// Layout: [header:32][sender:20][receiver:20][timestamps:16][len:4][payload:N]
// Total mínimo: 92 bytes + payload
// ============================================================================

import { Address, TemporalMessage, Timestamp, ArkheFrameType } from './types';
import { keccak256Sync } from '../crypto/keccak';
import { ARKHE_MAGIC_BYTES } from '../config/arkhe';

// Header binário: 80 bytes
const HEADER_SIZE = 80;
const FRAME_OVERHEAD = 16; // Cabeçalho do frame ARKHE

export class TemporalMessageEncoder {
  // Codifica mensagem para bytes (para envio via DataChannel)
  static encode(msg: TemporalMessage): Uint8Array {
    const contentBytes = new TextEncoder().encode(msg.content);
    const totalSize = FRAME_OVERHEAD + HEADER_SIZE + contentBytes.length + msg.payload.length;
    const buffer = new Uint8Array(totalSize);

    // Frame header
    buffer.set(ARKHE_MAGIC_BYTES, 0);
    buffer[4] = 0x04;              // version major
    buffer[5] = 0x39;              // version minor (= 4.3.9)
    buffer[6] = ArkheFrameType.TEMPORAL_MESSAGE;
    const seqNum = Date.now() & 0xFFFFFFFF;
    this.writeUint32(buffer, 8, seqNum);
    this.writeUint32(buffer, 12, totalSize - FRAME_OVERHEAD);

    // Message header
    buffer.set(hexToBytes(msg.sender.padEnd(40, '0')), 16);
    buffer.set(hexToBytes(msg.receiver.padEnd(40, '0')), 36);
    this.writeUint64(buffer, 56, msg.sourceTs);
    this.writeUint64(buffer, 64, msg.targetTs);
    this.writeUint32(buffer, 72, contentBytes.length);
    this.writeUint32(buffer, 76, HEADER_SIZE);  // payload offset
    this.writeUint16(buffer, 80, msg.signature?.length ?? 0);
    this.writeUint16(buffer, 82, msg.zkProof?.length ?? 0);

    // Content
    buffer.set(contentBytes, FRAME_OVERHEAD + HEADER_SIZE);

    // Payload
    if (msg.payload.length > 0) {
      buffer.set(msg.payload, FRAME_OVERHEAD + HEADER_SIZE + contentBytes.length);
    }

    return buffer;
  }

  // Decodifica bytes recebidos via DataChannel
  static decode(buffer: Uint8Array): TemporalMessage {
    // Verificar magic
    for (let i = 0; i < 4; i++) {
      if (buffer[i] !== ARKHE_MAGIC_BYTES[i]) {
        throw new Error('Invalid ARKHE frame magic');
      }
    }

    const msgType = buffer[6];
    if (msgType !== ArkheFrameType.TEMPORAL_MESSAGE) {
      throw new Error(`Expected TEMPORAL_MESSAGE (0x01), got 0x${msgType.toString(16)}`);
    }

    const sender = bytesToHex(buffer.slice(16, 36));
    const receiver = bytesToHex(buffer.slice(36, 56));
    const sourceTs = this.readUint64(buffer, 56);
    const targetTs = this.readUint64(buffer, 64);
    const contentLen = this.readUint32(buffer, 72);
    const payloadOffset = this.readUint32(buffer, 76);
    const sigLen = this.readUint16(buffer, 80);
    const zkLen = this.readUint16(buffer, 82);

    const contentStart = FRAME_OVERHEAD + HEADER_SIZE;
    const contentBytes = buffer.slice(contentStart, contentStart + contentLen);
    const content = new TextDecoder().decode(contentBytes);

    const payloadStart = FRAME_OVERHEAD + payloadOffset + contentLen;
    const payload = sigLen > 0
      ? buffer.slice(payloadStart, payloadStart + sigLen)
      : new Uint8Array(0);

    return {
      id: generateMessageId(buffer),
      sender,
      receiver,
      sourceTs,
      targetTs,
      content,
      payload,
      signature: sigLen > 0 ? buffer.slice(payloadStart, payloadStart + sigLen) : undefined,
      zkProof: zkLen > 0 ? buffer.slice(payloadStart + sigLen, payloadStart + sigLen + zkLen) : undefined,
    };
  }

  static computeHash(msg: TemporalMessage): Uint8Array {
    return keccak256Sync(
      new TextEncoder().encode(
        `${msg.sender}:${msg.receiver}:${msg.sourceTs}:${msg.targetTs}:${msg.content}`
      )
    );
  }

  static isTemporallyValid(msg: TemporalMessage, now: number): boolean {
    return msg.sourceTs <= now && msg.targetTs >= now;
  }

  static causalPrecedes(a: TemporalMessage, b: TemporalMessage): boolean {
    return a.targetTs <= b.sourceTs;
  }

  private static writeUint64(buf: Uint8Array, offset: number, value: number) {
    buf[offset] = (value >> 56) & 0xFF;
    buf[offset + 1] = (value >> 48) & 0xFF;
    buf[offset + 2] = (value >> 40) & 0xFF;
    buf[offset + 3] = (value >> 32) & 0xFF;
    buf[offset + 4] = (value >> 24) & 0xFF;
    buf[offset + 5] = (value >> 16) & 0xFF;
    buf[offset + 6] = (value >> 8) & 0xFF;
    buf[offset + 7] = value & 0xFF;
  }

  private static writeUint32(buf: Uint8Array, offset: number, value: number) {
    buf[offset] = (value >> 24) & 0xFF;
    buf[offset + 1] = (value >> 16) & 0xFF;
    buf[offset + 2] = (value >> 8) & 0xFF;
    buf[offset + 3] = value & 0xFF;
  }

  private static writeUint16(buf: Uint8Array, offset: number, value: number) {
    buf[offset] = (value >> 8) & 0xFF;
    buf[offset + 1] = value & 0xFF;
  }

  private static readUint64(buf: Uint8Array, offset: number): number {
    return Number(
      (BigInt(buf[offset]) << 56n) |
      (BigInt(buf[offset + 1]) << 48n) |
      (BigInt(buf[offset + 2]) << 40n) |
      (BigInt(buf[offset + 3]) << 32n) |
      (BigInt(buf[offset + 4]) << 24n) |
      (BigInt(buf[offset + 5]) << 16n) |
      (BigInt(buf[offset + 6]) << 8n) |
      BigInt(buf[offset + 7])
    );
  }

  private static readUint32(buf: Uint8Array, offset: number): number {
    return (buf[offset] << 24) | (buf[offset + 1] << 16) |
           (buf[offset + 2] << 8) | buf[offset + 3];
  }

  private static readUint16(buf: Uint8Array, offset: number): number {
    return (buf[offset] << 8) | buf[offset + 1];
  }
}

function hexToBytes(hex: string): Uint8Array {
  const cleanHex = hex.startsWith('0x') ? hex.slice(2) : hex;
  const bytes = new Uint8Array(cleanHex.length / 2);
  for (let i = 0; i < cleanHex.length; i += 2) {
    bytes[i / 2] = parseInt(cleanHex.slice(i, i + 2), 16);
  }
  return bytes;
}

function bytesToHex(bytes: Uint8Array): string {
    return '0x' + Array.from(bytes).map(b => b.toString(16).padStart(2, '0')).join('');
}

function generateMessageId(buffer: Uint8Array): string {
  const hash = keccak256Sync(buffer.slice(0, 80));
  return Array.from(hash.slice(0, 8)).map(b => b.toString(16).padStart(2, '0')).join('');
}
