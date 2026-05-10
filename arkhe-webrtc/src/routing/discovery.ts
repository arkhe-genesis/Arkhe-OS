// ============================================================================
// ARKHE Ω-TEMP — Peer Discovery
// ============================================================================
// Mecanismo de descoberta de peers na rede ARKHE.
// Combina mDNS (LAN), DHT (WAN) e relay server.
// ============================================================================

export interface DiscoveredPeer {
  address: string;
  capabilities: string[];
  latency: number;
  relayed: boolean;
  timestamp: number;
}

export interface DiscoveryConfig {
  enableMDNS: boolean;
  enableDHT: boolean;
  enableRelay: boolean;
  discoveryInterval: number;
  maxKnownPeers: number;
}

export class PeerDiscovery {
  private knownPeers: Map<string, DiscoveredPeer> = new Map();
  private config: DiscoveryConfig;
  private broadcastChannel: BroadcastChannel | null = null;
  private discoveryTimer: ReturnType<typeof setInterval> | null = null;

  constructor(config: DiscoveryConfig) {
    this.config = {
      enableMDNS: config.enableMDNS ?? true,
      enableDHT: config.enableDHT ?? true,
      enableRelay: config.enableRelay ?? true,
      discoveryInterval: config.discoveryInterval ?? 5000,
      maxKnownPeers: config.maxKnownPeers ?? 1000,
    };
  }

  start(): void {
    // Broadcast Channel (mesma aba/navegador)
    try {
      this.broadcastChannel = new BroadcastChannel('arkhe-discovery');
      this.broadcastChannel.onmessage = (event) => {
        this.handleBroadcastMessage(event.data);
      };
    } catch (e) {
      console.warn('[Discovery] BroadcastChannel não suportado');
    }

    // Anúncio periódico
    this.discoveryTimer = setInterval(() => {
      this.announcePresence();
      this.cleanupStalePeers();
    }, this.config.discoveryInterval);

    console.log('[Discovery] Iniciado');
  }

  stop(): void {
    if (this.discoveryTimer) {
      clearInterval(this.discoveryTimer);
    }
    if (this.broadcastChannel) {
      this.broadcastChannel.close();
    }
  }

  // Anunciar presença na rede local
  private announcePresence(): void {
    const announcement = {
      type: 'arkhe-announce',
      address: this.generateAddress(),
      timestamp: Date.now(),
      capabilities: ['temporal', 'consensus', 'routing', 'merkle', 'zk'],
      protocols: ['arkhe-v1'],
    };

    // Broadcast Channel
    if (this.broadcastChannel) {
      try {
        this.broadcastChannel.postMessage(announcement);
      } catch (e) {
        // Canal fechado
      }
    }
  }

  handleBroadcastMessage(data: any): void {
    if (data.type !== 'arkhe-announce') return;
    if (data.address === this.getMyAddress()) return;

    const peer: DiscoveredPeer = {
      address: data.address,
      capabilities: data.capabilities || [],
      latency: 0,
      relayed: false,
      timestamp: data.timestamp || Date.now(),
    };

    this.addPeer(peer);
  }

  addPeer(peer: DiscoveredPeer): void {
    const existing = this.knownPeers.get(peer.address);

    if (existing) {
      // Atualizar timestamp
      existing.timestamp = Date.now();
      existing.latency = peer.latency;
    } else {
      // Evictar se necessário
      if (this.knownPeers.size >= this.config.maxKnownPeers) {
        this.evictOldestPeer();
      }
      this.knownPeers.set(peer.address, peer);
    }
  }

  getPeers(): DiscoveredPeer[] {
    return Array.from(this.knownPeers.values())
      .filter(p => Date.now() - p.timestamp < 60000) // Menos de 60s antigo
      .sort((a, b) => a.latency - b.latency); // Melhor latência primeiro
  }

  getBestPeers(count: number = 10): DiscoveredPeer[] {
    return this.getPeers().slice(0, count);
  }

  removePeer(address: string): void {
    this.knownPeers.delete(address);
  }

  isPeerKnown(address: string): boolean {
    return this.knownPeers.has(address);
  }

  private getMyAddress(): string {
    // Retornar endereço do nó local
    return localStorage.getItem('arkhe-address') || 'unknown';
  }

  private generateAddress(): string {
    // Gerar endereço ARKHE
    const array = new Uint8Array(20);
    crypto.getRandomValues(array);
    return '0x' + Array.from(array).map(b => b.toString(16).padStart(2, '0')).join('');
  }

  private cleanupStalePeers(): void {
    const now = Date.now();
    for (const [address, peer] of this.knownPeers) {
      if (now - peer.timestamp > 120000) { // 2 minutos
        this.knownPeers.delete(address);
      }
    }
  }

  private evictOldestPeer(): void {
    let oldest: string | null = null;
    let oldestTimestamp = Date.now();

    for (const [address, peer] of this.knownPeers) {
      if (peer.timestamp < oldestTimestamp) {
        oldestTimestamp = peer.timestamp;
        oldest = address;
      }
    }

    if (oldest) {
      this.knownPeers.delete(oldest);
    }
  }
}
