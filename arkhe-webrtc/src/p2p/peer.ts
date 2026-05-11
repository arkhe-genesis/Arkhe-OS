// ============================================================================
// ARKHE Ω-TEMP — WebRTC Peer Wrapper
// ============================================================================
// Encapsula a complexidade do WebRTC SimplePeer, expondo apenas
// as operações necessárias para o protocolo ARKHE.
// ============================================================================

import SimplePeer from 'simple-peer';
import {
  Address, TemporalMessage, PeerInfo, ArkheFrame, ArkheFrameType,
} from '../core/types';
import { TemporalMessageEncoder } from '../core/temporal-message';
import { ArkheProtocol } from './protocol';

export enum PeerState {
  DISCONNECTED = 'disconnected',
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  SYNCHRONIZING = 'synchronizing',
  ACTIVE = 'active',
}

export interface PeerConfig {
  iceConfig: RTCConfiguration;
  isInitiator: boolean;
  maxMessageSize: number;
}

export class ArkhePeer {
  public peer: SimplePeer.Instance;
  public address: Address;
  public info: PeerInfo;
  public state: PeerState = PeerState.DISCONNECTED;
  public messagesSent: number = 0;
  public messagesReceived: number = 0;
  private latencySamples: number[] = [];
  private lastSeen: number = 0;

  private messageHandlers: Map<ArkheFrameType, (frame: ArkheFrame) => void> = new Map();
  private onMessageCb: (from: Address, msg: TemporalMessage) => void;
  private onBlockCb: (from: Address, block: any) => void;
  private onDisconnectCb: (address: Address) => void;

  constructor(
    address: Address,
    config: PeerConfig,
    onMessage: (from: Address, msg: TemporalMessage) => void,
    onBlock: (from: Address, block: any) => void,
    onDisconnect: (address: Address) => void,
  ) {
    this.address = address;
    this.onMessageCb = onMessage;
    this.onBlockCb = onBlock;
    this.onDisconnectCb = onDisconnect;
    this.info = this.createPeerInfo(address);

    this.peer = new SimplePeer({
      initiator: config.isInitiator,
      trickle: true,
      config: config.iceConfig,
      channelConfig: { ordered: true, maxRetransmits: 3 },
    });

    this.setupHandlers();
  }

  private createPeerInfo(address: string): PeerInfo {
    return {
      address,
      capabilities: ['temporal', 'consensus', 'routing', 'merkle', 'zk'],
      blockHeight: 0,
      consistencyScore: 1.0,
      latency: 0,
      isRelayed: false,
    };
  }

  private setupHandlers(): void {
    this.peer.on('error', (err: Error) => {
      console.error(`[ARKHE Peer ${this.address}] Error:`, err.message);
    });

    this.peer.on('signal', (data: any) => {
      this.state = PeerState.CONNECTING;
      this.emitSignal(data);
    });

    this.peer.on('connect', () => {
      this.state = PeerState.CONNECTED;
      this.lastSeen = Date.now();
      console.log(`[ARKHE] Connected to ${this.address}`);
      this.sendHello();
    });

    this.peer.on('data', (data: Buffer) => {
      this.handleData(new Uint8Array(data.buffer));
    });

    this.peer.on('close', () => {
      this.state = PeerState.DISCONNECTED;
      this.onDisconnectCb(this.address);
    });
  }

  private emitSignal(data: any): void {
    const event = new CustomEvent('arkhe-signal', {
        detail: { targetAddress: this.address, signal: data }
    });
    // This is generally used in browser environments; fallback if missing.
    if (typeof window !== 'undefined') {
        window.dispatchEvent(event);
    }
  }

  private handleData(rawData: Uint8Array): void {
    try {
      this.lastSeen = Date.now();
      const frame = ArkheProtocol.deserializeFrame(rawData);
      if (!frame) return;

      this.messagesReceived++;

      if (frame.header.type === ArkheFrameType.TEMPORAL_MESSAGE) {
        const msg = TemporalMessageEncoder.decode(frame.payload);
        this.onMessageCb(this.address, msg);
      } else if (frame.header.type === ArkheFrameType.BLOCK_ANNOUNCE) {
        // Handle block announcement
        console.log(`[Peer ${this.address}] Block received`);
      } else if (frame.header.type === ArkheFrameType.PEER_HELLO) {
        this.sendHelloAck();
      } else {
        const handler = this.messageHandlers.get(frame.header.type);
        if (handler) handler(frame);
      }
    } catch (err) {
      console.error(`[Peer ${this.address}] Data error:`, err);
    }
  }

  // === PUBLIC API ===

  sendMessage(msg: TemporalMessage): void {
    const encoded = TemporalMessageEncoder.encode(msg);
    const frame = ArkheProtocol.createFrame(
      ArkheFrameType.TEMPORAL_MESSAGE, encoded
    );
    const raw = ArkheProtocol.serializeFrame(frame);
    this.peer.send(Buffer.from(raw));
    this.messagesSent++;
  }

  sendHello(): void {
    const payload = new Uint8Array(1);
    payload[0] = 0x01;
    const frame = ArkheProtocol.createFrame(ArkheFrameType.PEER_HELLO, payload);
    this.peer.send(Buffer.from(ArkheProtocol.serializeFrame(frame)));
  }

  sendHelloAck(): void {
    const payload = new Uint8Array(1);
    payload[0] = 0x02;
    const frame = ArkheProtocol.createFrame(ArkheFrameType.PEER_HELLO_ACK, payload);
    this.peer.send(Buffer.from(ArkheProtocol.serializeFrame(frame)));
  }

  sendPing(): void {
    const payload = new Uint8Array(8);
    new DataView(payload.buffer).setFloat64(0, performance.now(), false);
    const frame = ArkheProtocol.createFrame(ArkheFrameType.PING, payload);
    this.peer.send(Buffer.from(ArkheProtocol.serializeFrame(frame)));
  }

  getLatency(): number {
    return this.latencySamples.length > 0
      ? this.latencySamples.reduce((a, b) => a + b) / this.latencySamples.length
      : 0;
  }

  getLastSeen(): number {
    return this.lastSeen;
  }

  isReady(): boolean {
    // SimplePeer uses .connected boolean sometimes or peer.readyState, here we try to detect state
    return this.peer.connected;
  }

  get isRelayed(): boolean {
      return false; // not implemented
  }

  destroy(): void {
    this.peer.destroy();
  }
}
