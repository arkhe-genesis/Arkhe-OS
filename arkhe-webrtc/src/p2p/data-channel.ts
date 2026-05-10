// ============================================================================
// ARKHE Ω-TEMP — DataChannel Manager
// ============================================================================
// Gerencia múltiplos DataChannels por peer para diferentes propósitos:
//   - canal de dados principal (mensagens temporais)
//   - canal de consenso (votação)
//   - canal de sync (Merkle sync)
//   - canal de streaming (block streaming)
// ============================================================================

export interface ChannelConfig {
  label: string;
  ordered: boolean;
  maxRetransmits: number;
  negotiated: boolean;
  protocol: string;
}

export enum ChannelState {
  CONNECTING = 'connecting',
  OPEN = 'open',
  CLOSING = 'closing',
  CLOSED = 'closed',
}

export interface ChannelMessage {
  type: string;
  data: Uint8Array;
  timestamp: number;
  seqNum: number;
}

export type ChannelHandler = (message: ChannelMessage) => void;

export class DataChannelManager {
  private peerConnection: RTCPeerConnection;
  private channels: Map<string, RTCDataChannel> = new Map();
  private handlers: Map<string, Set<ChannelHandler>> = new Map();
  private bufferSize: Map<string, number> = new Map();

  // Configurações padrão para cada tipo de canal
  static readonly CHANNEL_CONFIGS: Record<string, ChannelConfig> = {
    main: {
      label: 'arkhe-v1',
      ordered: true,
      maxRetransmits: 3,
      negotiated: false,
      protocol: 'arkhe-main',
    },
    consensus: {
      label: 'arkhe-consensus',
      ordered: true,
      maxRetransmits: 0,  // Confiável - sem perda
      negotiated: false,
      protocol: 'arkhe-consensus',
    },
    sync: {
      label: 'arkhe-sync',
      ordered: true,
      maxRetransmits: 0,  // Confiável para sync
      negotiated: false,
      protocol: 'arkhe-sync',
    },
    streaming: {
      label: 'arkhe-stream',
      ordered: false,     // Não ordenado para performance
      maxRetransmits: -1, // Unreliable - permite perda
      negotiated: false,
      protocol: 'arkhe-stream',
    },
  };

  constructor(peerConnection: RTCPeerConnection) {
    this.peerConnection = peerConnection;
    this.setupDefaultChannels();
  }

  private setupDefaultChannels(): void {
    // Criar canais padrão
    this.createChannel('main');
    this.createChannel('consensus');
    this.createChannel('sync');
  }

  createChannel(type: string): RTCDataChannel {
    const config = DataChannelManager.CHANNEL_CONFIGS[type];
    if (!config) {
      throw new Error(`Unknown channel type: ${type}`);
    }

    if (this.channels.has(type)) {
      const existing = this.channels.get(type)!;
      if (existing.readyState !== 'closed') {
        return existing;
      }
    }

    const channel = this.peerConnection.createDataChannel(config.label, {
      ordered: config.ordered,
      maxRetransmits: config.maxRetransmits === -1 ? undefined : config.maxRetransmits,
      maxPacketLifeTime: config.maxRetransmits === -1 ? 500 : undefined,
      negotiated: config.negotiated,
      protocol: config.protocol,
    });

    channel.binaryType = 'arraybuffer';

    channel.onopen = () => {
      console.log(`[DataChannel] ${type} opened`);
      this.notifyHandlers(type, {
        type: 'channel-open',
        data: new Uint8Array(),
        timestamp: Date.now(),
        seqNum: 0,
      });
    };

    channel.onclose = () => {
      console.log(`[DataChannel] ${type} closed`);
      this.channels.delete(type);
    };

    channel.onmessage = (event: MessageEvent) => {
      const data = new Uint8Array(event.data as ArrayBuffer);
      this.handleChannelMessage(type, data);
    };

    channel.onerror = (error: Event) => {
      console.error(`[DataChannel] ${type} error:`, error);
    };

    channel.onbufferedamountlow = () => {
      this.bufferSize.set(type, channel.bufferedAmount);
    };

    this.channels.set(type, channel);
    return channel;
  }

  // Enviar dados via canal específico
  send(type: string, data: Uint8Array): boolean {
    const channel = this.channels.get(type);
    if (!channel || channel.readyState !== 'open') {
      return false;
    }

    try {
      // Verificar buffer
      const bufferedAmount = channel.bufferedAmount;
      const bufferLimit = 16 * 1024 * 1024; // 16MB buffer limit

      if (bufferedAmount > bufferLimit) {
        console.warn(`[DataChannel] ${type} buffer full (${bufferedAmount} bytes)`);
        return false;
      }

      channel.send(data.buffer as ArrayBuffer);
      return true;
    } catch (err) {
      console.error(`[DataChannel] Error sending on ${type}:`, err);
      return false;
    }
  }

  // Enviar fragmentos grandes (automático)
  sendFragmented(
    type: string,
    data: Uint8Array,
    fragmentSize: number = 16384 // 16KB fragments
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      const channel = this.channels.get(type);
      if (!channel || channel.readyState !== 'open') {
        reject(new Error(`Channel ${type} not open`));
        return;
      }

      // Header: [totalSize:4][fragmentIndex:4][totalFragments:4][data:...]
      const totalFragments = Math.ceil(data.byteLength / fragmentSize);

      for (let i = 0; i < totalFragments; i++) {
        const start = i * fragmentSize;
        const end = Math.min(start + fragmentSize, data.byteLength);
        const fragment = data.slice(start, end);

        const header = new Uint8Array(12);
        const view = new DataView(header.buffer);
        view.setUint32(0, data.byteLength, false);     // Total size
        view.setUint32(4, i, false);                     // Fragment index
        view.setUint32(8, totalFragments, false);        // Total fragments

        const packet = new Uint8Array(header.length + fragment.length);
        packet.set(header);
        packet.set(fragment, header.length);

        try {
          channel.send(packet.buffer);
        } catch (err) {
          reject(err);
          return;
        }
      }

      resolve();
    });
  }

  private handleChannelMessage(type: string, data: Uint8Array): void {
    // Verificar se é fragmentado
    if (data.length >= 12) {
      const view = new DataView(data.buffer);
      const totalSize = view.getUint32(0, false);
      const fragmentIndex = view.getUint32(4, false);
      const totalFragments = view.getUint32(8, false);

      if (totalFragments > 1) {
        // Reconstruir mensagem fragmentada
        this.reassembleFragment(type, data, totalSize, fragmentIndex, totalFragments);
        return;
      }
    }

    // Mensagem simples
    this.notifyHandlers(type, {
      type: 'message',
      data,
      timestamp: Date.now(),
      seqNum: 0,
    });
  }

  // Reassemblagem de fragmentos
  private fragmentBuffers: Map<string, Map<number, Uint8Array>> = new Map();
  private fragmentMetadata: Map<string, {
    received: number;
    total: number;
    buffer: Uint8Array;
  }> = new Map();

  private reassembleFragment(
    type: string,
    fragment: Uint8Array,
    totalSize: number,
    fragmentIndex: number,
    totalFragments: number
  ): void {
    const key = `${type}_fragment`;
    let meta = this.fragmentMetadata.get(key);

    if (!meta || meta.total !== totalFragments || meta.buffer.byteLength !== totalSize) {
      meta = {
        received: 0,
        total: totalFragments,
        buffer: new Uint8Array(totalSize),
      };
      this.fragmentMetadata.set(key, meta);
    }

    const headerSize = 12;
    const fragmentData = fragment.slice(headerSize);
    const offset = fragmentIndex * (fragment.byteLength - headerSize);

    // Calcular tamanho real deste fragmento
    const fragmentDataSize = Math.min(
      fragmentData.length,
      totalSize - offset
    );

    meta.buffer.set(fragmentData.subarray(0, fragmentDataSize), offset);
    meta.received++;

    if (meta.received === meta.total) {
      // Mensagem completa
      this.notifyHandlers(type, {
        type: 'message',
        data: meta.buffer,
        timestamp: Date.now(),
        seqNum: 0,
      });

      this.fragmentMetadata.delete(key);
    }
  }

  // Registrar handlers
  on(type: string, handler: ChannelHandler): void {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, new Set());
    }
    this.handlers.get(type)!.add(handler);
  }

  off(type: string, handler: ChannelHandler): void {
    this.handlers.get(type)?.delete(handler);
  }

  private notifyHandlers(type: string, message: ChannelMessage): void {
    const handlers = this.handlers.get(type);
    if (handlers) {
      handlers.forEach(h => {
        try {
          h(message);
        } catch (err) {
          console.error(`[DataChannel] Handler error:`, err);
        }
      });
    }
  }

  // Monitoramento
  getStats(type: string): {
    bufferedAmount: number;
    readyState: string;
    protocol: string;
  } | null {
    const channel = this.channels.get(type);
    if (!channel) return null;

    return {
      bufferedAmount: channel.bufferedAmount,
      readyState: channel.readyState,
      protocol: channel.protocol,
    };
  }

  close(type?: string): void {
    if (type) {
      const channel = this.channels.get(type);
      if (channel) {
        channel.close();
        this.channels.delete(type);
      }
    } else {
      this.channels.forEach((ch) => ch.close());
      this.channels.clear();
    }
  }
}
