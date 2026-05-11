// ============================================================================
// ARKHE Ω-TEMP — Signaling Client
// ============================================================================
// Gerencia a comunicação com o servidor de sinalização WebSocket.
// Responsável por:
//   - Join/leave de rooms
//   - Troca de offers/answers/ICE candidates
//   - Presença de peers
// ============================================================================

export interface SignalingConfig {
  url: string;
  roomId: string;
  nodeInfo: any;
  reconnect: boolean;
  maxReconnectAttempts: number;
  reconnectDelay: number;
}

export interface SignalingMessage {
  type: string;
  from?: string;
  to?: string;
  roomId?: string;
  offer?: RTCSessionDescriptionInit;
  answer?: RTCSessionDescriptionInit;
  candidate?: RTCIceCandidateInit;
  nodeInfo?: any;
  peers?: any[];
  error?: string;
}

export class SignalingClient {
  private ws: WebSocket | null = null;
  private config: SignalingConfig;
  private reconnectAttempts: number = 0;
  private messageHandlers: Map<string, (msg: SignalingMessage) => void> = new Map();
  private connectionId: string | null = null;

  constructor(config: SignalingConfig) {
    this.config = config;
  }

  async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.config.url);

        this.ws.onopen = () => {
          console.log('[Signaling] Connected');
          this.joinRoom();
          resolve();
        };

        this.ws.onmessage = (event: MessageEvent) => {
          try {
            const data: SignalingMessage = JSON.parse(event.data);
            this.handleMessage(data);
          } catch (err) {
            console.error('[Signaling] Error parsing message:', err);
          }
        };

        this.ws.onclose = (event: CloseEvent) => {
          console.log(`[Signaling] Closed (code: ${event.code}, reason: ${event.reason})`);
          this.handleDisconnection();
        };

        this.ws.onerror = (err: Event) => {
          console.error('[Signaling] Error:', err);
          reject(err);
        };
      } catch (err) {
        reject(err);
      }
    });
  }

  private joinRoom(): void {
    this.sendMessage({
      type: 'join-room',
      roomId: this.config.roomId,
      nodeInfo: this.config.nodeInfo,
    });
  }

  onMessage(type: string, handler: (msg: SignalingMessage) => void): void {
    this.messageHandlers.set(type, handler);
  }

  offMessage(type: string): void {
    this.messageHandlers.delete(type);
  }

  private handleMessage(msg: SignalingMessage): void {
    const handler = this.messageHandlers.get(msg.type);
    if (handler) {
      handler(msg);
    }

    // Ações automáticas
    switch (msg.type) {
      case 'peer-joined':
        console.log(`[Signaling] Peer joined: ${msg.from}`);
        break;
      case 'peer-left':
        console.log(`[Signaling] Peer left: ${msg.from}`);
        break;
      case 'room-full':
        console.log('[Signaling] Room is full');
        break;
    }
  }

  sendMessage(msg: SignalingMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(msg));
    } else {
      console.warn('[Signaling] WebSocket not ready');
    }
  }

  // Enviar offer para peer específico
  sendOffer(to: string, offer: RTCSessionDescriptionInit, nodeInfo: any): void {
    this.sendMessage({
      type: 'signal-offer',
      to,
      from: this.config.nodeInfo.address,
      offer,
      nodeInfo,
    });
  }

  // Enviar answer para peer específico
  sendAnswer(to: string, answer: RTCSessionDescriptionInit): void {
    this.sendMessage({
      type: 'signal-answer',
      to,
      from: this.config.nodeInfo.address,
      answer,
    });
  }

  // Enviar ICE candidate
  sendCandidate(to: string, candidate: RTCIceCandidateInit): void {
    this.sendMessage({
      type: 'signal-ice-candidate',
      to,
      from: this.config.nodeInfo.address,
      candidate,
    });
  }

  private handleDisconnection(): void {
    if (!this.config.reconnect) return;

    if (this.reconnectAttempts < this.config.maxReconnectAttempts) {
      const delay = this.config.reconnectDelay * Math.pow(2, this.reconnectAttempts);
      console.log(`[Signaling] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts + 1})`);

      setTimeout(() => {
        this.reconnectAttempts++;
        this.connect().catch(console.error);
      }, delay);
    } else {
      console.error('[Signaling] Max reconnection attempts reached');
    }
  }

  getConnectionId(): string | null {
    return this.connectionId;
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  disconnect(): void {
    this.config.reconnect = false;
    this.ws?.close();
  }
}
