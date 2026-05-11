import {
  Address, TemporalMessage, PeerInfo, RouteResult, ArkheFrame, ArkheFrameType, MeshMetrics
} from '../core/types';
import { ArkhePeer } from './peer';
import { TemporalHashChain } from '../core/hash-chain';
import { RoutingTable } from '../routing/router';
import { GossipProtocol } from '../routing/gossip';
import { generateAddressSync } from '../core/address';
import { TemporalMessageEncoder } from '../core/temporal-message';
import { TemporalConsistencyOracle } from '../consensus/oracle';

export interface MeshConfig {
  iceConfig: RTCConfiguration;
  signalingUrl: string;
  maxPeers: number;
  roomId: string;
  nodeName: string;
}

export enum MeshState {
  INITIALIZING = 'initializing',
  CONNECTING_SIGNALING = 'connecting_signaling',
  WAITING_PEERS = 'waiting_peers',
  ACTIVE = 'active',
  DEGRADED = 'degraded',
  ISOLATED = 'isolated',
}

export class ArkheMesh {
  private peers: Map<Address, ArkhePeer> = new Map();
  private myAddress: Address;
  private state: MeshState = MeshState.INITIALIZING;
  private signalingSocket: WebSocket | null = null;
  private chain: TemporalHashChain;
  private routingTable: RoutingTable;
  private gossip: GossipProtocol;
  private pendingConnections: Map<string, ArkhePeer> = new Map();
  private config: MeshConfig;
  private reconnectAttempts: Map<Address, number> = new Map();

  constructor(config: MeshConfig) {
    this.config = config;
    this.myAddress = generateAddressSync(config.nodeName);
    this.chain = new TemporalHashChain();
    this.routingTable = new RoutingTable(this.myAddress);
    this.gossip = new GossipProtocol(this.broadcastMessage.bind(this));
    console.log(`[ARKHE Mesh] Nó inicializado: ${this.myAddress}`);
  }

  async start(): Promise<void> {
    this.state = MeshState.CONNECTING_SIGNALING;
    await this.connectSignaling();
    this.setupEventHandlers();
    console.log(`[ARKHE Mesh] Nó ${this.myAddress} ativo`);
  }

  private async connectSignaling(): Promise<void> {
    return new Promise((resolve, reject) => {
      // In a node environment ws is required. In browser WebSocket is native.
      // This implementation tries to handle generic WebSocket.
      let WS: typeof WebSocket;
      if (typeof window !== 'undefined' && typeof window.WebSocket !== 'undefined') {
          WS = window.WebSocket;
      } else {
          try { WS = require('ws'); } catch (e) { throw new Error('WebSocket not available'); }
      }

      const ws = new WS(this.config.signalingUrl);
      ws.onopen = () => {
        this.signalingSocket = ws;
        this.sendSignalingMessage({
          type: 'join-room',
          roomId: this.config.roomId,
          nodeInfo: this.createNodeInfo(),
        });
        resolve();
      };
      ws.onmessage = (event: MessageEvent) => {
        this.handleSignalingMessage(JSON.parse(event.data));
      };
      ws.onclose = () => {
        this.signalingSocket = null;
        setTimeout(() => {
          if (this.state !== MeshState.ISOLATED) {
            this.connectSignaling().catch(console.error);
          }
        }, 3000);
      };
      ws.onerror = reject;
    });
  }

  private setupEventHandlers() {
      if (typeof window !== 'undefined') {
          window.addEventListener('arkhe-signal', (event: any) => {
              const { targetAddress, signal } = event.detail;
              this.handlePeerSignal(targetAddress, signal);
          });
      }
      setInterval(() => this.heartbeat(), 5000);
  }

  private async handlePeerSignal(peerAddress: Address, signal: any): Promise<void> {
    this.sendSignalingMessage({
      type: 'signal-ice-candidate',
      from: this.myAddress,
      to: peerAddress,
      candidate: signal,
    });
  }

  private handleSignalingMessage(data: any): void {
    switch (data.type) {
      case 'peer-joined': this.onPeerJoined(data.peerInfo); break;
      case 'peer-left': this.onPeerLeft(data.peerAddress); break;
      case 'signal-offer': this.handleOffer(data); break;
      case 'signal-answer': this.handleAnswer(data); break;
      case 'signal-ice-candidate': this.handleIceCandidate(data); break;
      case 'room-update': this.onRoomUpdate(data.peers); break;
    }
  }

  private onPeerJoined(peerInfo: any): void {
    if (this.peers.has(peerInfo.address) ||
        this.peers.size >= this.config.maxPeers) return;

    const peer = this.createPeer(peerInfo.address, peerInfo, true);
    peer.peer.on('signal', (offer: any) => {
      this.sendSignalingMessage({
        type: 'signal-offer',
        from: this.myAddress,
        to: peerInfo.address,
        offer,
        nodeInfo: this.createNodeInfo(),
      });
    });
  }

  private onPeerLeft(peerAddress: Address): void {
    const peer = this.peers.get(peerAddress);
    if (peer) {
      peer.destroy();
      this.peers.delete(peerAddress);
      this.routingTable.removePeer(peerAddress);
      this.updateMeshState();
    }
  }

  private handleOffer(data: any): void {
    if (this.peers.has(data.from)) return;
    const peer = this.createPeer(data.from, data.nodeInfo, false);
    peer.peer.signal(data.offer);
    this.pendingConnections.set(data.from, peer);
  }

  private handleAnswer(data: any): void {
    const peer = this.pendingConnections.get(data.from);
    if (peer) {
      peer.peer.signal(data.answer);
      this.pendingConnections.delete(data.from);
    }
  }

  private handleIceCandidate(data: any): void {
    const peer = this.peers.get(data.from) || this.pendingConnections.get(data.from);
    if (peer) peer.peer.signal(data.candidate);
  }

  private onRoomUpdate(peerList: any[]): void {
    peerList.forEach((info: any) => {
      if (info.address !== this.myAddress && !this.peers.has(info.address)) {
        setTimeout(() => this.onPeerJoined(info), Math.random() * 2000);
      }
    });
    this.updateMeshState();
  }

  private createPeer(address: Address, info: any, isInitiator: boolean): ArkhePeer {
    const peer = new ArkhePeer(
      address,
      { iceConfig: this.config.iceConfig, isInitiator, maxMessageSize: 65536 },
      (from, msg) => this.onMessageReceived(from, msg),
      (from, block) => this.onBlockReceived(from, block),
      (addr) => this.onPeerDisconnected(addr),
    );
    this.peers.set(address, peer);
    this.routingTable.addPeer(info);
    return peer;
  }

  private onPeerDisconnected(address: Address): void {
    const peer = this.peers.get(address);
    if (peer) {
      peer.destroy();
      this.peers.delete(address);
      this.routingTable.removePeer(address);
      this.scheduleReconnection(address);
      this.updateMeshState();
    }
  }

  private scheduleReconnection(address: Address): void {
    const attempts = (this.reconnectAttempts.get(address) || 0) + 1;
    this.reconnectAttempts.set(address, attempts);
    const delay = Math.min(1000 * Math.pow(2, attempts - 1), 30000);
    setTimeout(() => {
      if (!this.peers.has(address) && this.signalingSocket) {
        this.sendSignalingMessage({
          type: 'reconnect-request',
          from: this.myAddress,
          to: address,
        });
      }
    }, delay);
  }

  private onMessageReceived(from: Address, msg: TemporalMessage): void {
    const now = (performance.timeOrigin || 0) + performance.now() * 1000;
    if (!TemporalMessageEncoder.isTemporallyValid(msg, now)) return;

    const oracle = TemporalConsistencyOracle.getInstance();
    const report = oracle.evaluate(msg);

    if (report.score < 0.5 || report.pruned) return;
    this.processMessage(msg);
    this.gossip.propagate(msg);
  }

  private onBlockReceived(from: Address, block: any): void {
    if (this.validateRemoteBlock(block)) {
      this.chain.appendBlock(block.messages, block.prevHash);
    }
  }

  private broadcastMessage(frame: ArkheFrame, excluded: Address[] = []): void {
    this.peers.forEach((peer, address) => {
      if (!excluded.includes(address) && peer.isReady()) {
        try {
            peer.sendMessage(TemporalMessageEncoder.decode(frame.payload));
        } catch (e) { console.error(e); }
      }
    });
  }

  private processMessage(msg: TemporalMessage): void { /* ... */ }
  private validateRemoteBlock(block: any): boolean { /* ... */ return true; }
  private updateMeshState(): void {
    const active = this.getActivePeers().length;
    if (active === 0) this.state = MeshState.ISOLATED;
    else if (active < this.config.maxPeers * 0.3) this.state = MeshState.DEGRADED;
    else this.state = MeshState.ACTIVE;
  }

  private heartbeat(): void {
    this.peers.forEach((peer, address) => {
      peer.sendPing();
      if (Date.now() - peer.getLastSeen() > 30000) {
        peer.destroy();
        this.peers.delete(address);
        this.routingTable.removePeer(address);
        this.scheduleReconnection(address);
      }
    });
  }

  getActivePeers(): ArkhePeer[] {
    return Array.from(this.peers.values()).filter(p => p.isReady());
  }

  getMeshMetrics(): MeshMetrics {
    const activePeers = this.getActivePeers();
    return {
      totalPeers: this.peers.size,
      activePeers: activePeers.length,
      relayedPeers: activePeers.filter(p => p.isRelayed).length,
      messagesSent: Array.from(this.peers.values())
        .reduce((s, p) => s + p.messagesSent, 0),
      messagesReceived: Array.from(this.peers.values())
        .reduce((s, p) => s + p.messagesReceived, 0),
      avgLatencyMs: activePeers.length > 0
        ? activePeers.reduce((s, p) => s + p.getLatency(), 0) / activePeers.length
        : 0,
      routingTableSize: this.routingTable.size(),
      chainLength: this.chain.length,
      consensusScore: 1.0,
    };
  }

  private createNodeInfo(): any {
    return {
      address: this.myAddress,
      capabilities: ['temporal', 'consensus', 'routing', 'merkle', 'zk'],
      blockHeight: this.chain.length,
      consistencyScore: 1.0,
    };
  }

  private sendSignalingMessage(data: any): void {
    if (this.signalingSocket?.readyState === WebSocket.OPEN) {
      this.signalingSocket.send(JSON.stringify(data));
    }
  }
}
