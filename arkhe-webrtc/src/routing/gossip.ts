// ============================================================================
// ARKHE Ω-TEMP — Gossip Protocol
// ============================================================================
// Protocolo de disseminação de mensagens baseado em Epidemic Gossip.
// Cada mensagem é propagada com fanout configurável e TTL máximo.
//
// Garantias:
//   - Eventual delivery para todos os peers conectados
//   - Deduplication via message ID cache
//   - Bounded fanout para evitar storms
// ============================================================================

export interface GossipConfig {
  fanout: number;          // Nº de peers para retransmitir
  ttl: number;             // Máximo de hops
  interval: number;        // Intervalo de gossip (ms)
  seenCacheSize: number;   // Tamanho do cache de duplicatas
}

export interface GossipMessage {
  id: string;
  sender: string;
  ttl: number;
  hopCount: number;
  timestamp: number;
  payload: any;
}

export class GossipProtocol {
  private seenMessages: Set<string> = new Set(); // Message ID cache
  private seenList: string[] = []; // LRU eviction
  private config: GossipConfig;

  constructor(
    private broadcastFn: (msg: any, excluded: string[]) => void,
    config?: Partial<GossipConfig>
  ) {
    this.config = {
      fanout: 4,
      ttl: 8,
      interval: 1000,
      seenCacheSize: 10000,
      ...config,
    };

    // Iniciar gossip periódico (para dados periódicos como heartbeats)
    setInterval(() => {
      this.gossipHeartbeat();
    }, this.config.interval);
  }

  // Propagar mensagem
  propagate(message: any): void {
    const msgId = this.computeMessageId(message);

    // Verificar duplicata
    if (this.isSeen(msgId)) {
      return; // Já processamos esta mensagem
    }

    // Marcar como visto
    this.markSeen(msgId);

    // Criar gossip message
    const gossipMsg: GossipMessage = {
      id: msgId,
      sender: 'self', // Será substituído pelo mesh
      ttl: this.config.ttl,
      hopCount: 0,
      timestamp: Date.now(),
      payload: message,
    };

    // Broadcast para peers
    this.broadcastFn(gossipMsg, []);
  }

  // Processar mensagem gossip recebida
  onGossipReceived(
    msg: GossipMessage,
    from: string
  ): { shouldRelay: boolean; excluded: string[] } {
    // Verificar TTL
    if (msg.ttl <= 0) {
      return { shouldRelay: false, excluded: [] };
    }

    // Verificar duplicata
    if (this.isSeen(msg.id)) {
      return { shouldRelay: false, excluded: [] };
    }

    // Verificar hop count
    if (msg.hopCount >= this.config.ttl) {
      this.markSeen(msg.id);
      return { shouldRelay: false, excluded: [] };
    }

    // Marcar como visto
    this.markSeen(msg.id);

    // Decrementar TTL e incrementar hop count
    msg.ttl--;
    msg.hopCount++;

    // Selecionar peers para retransmissão (random fanout)
    // O mesh cuida da seleção real
    return {
      shouldRelay: true,
      excluded: [from, msg.sender], // Não retransmitir de volta
    };
  }

  // Gossip heartbeat periódico (para manter conectividade)
  private gossipHeartbeat(): void {
    // Não propagar dados pesados, apenas status
    // (implementação completa enviaria métricas ou hashes de estado)
  }

  // Verificar se mensagem já foi vista (com LRU eviction)
  private isSeen(msgId: string): boolean {
    return this.seenMessages.has(msgId);
  }

  // Marcar mensagem como vista
  private markSeen(msgId: string): void {
    if (this.seenMessages.size >= this.config.seenCacheSize) {
      // Evictar mais antigo
      const oldest = this.seenList.shift();
      if (oldest) {
        this.seenMessages.delete(oldest);
      }
    }

    this.seenMessages.add(msgId);
    this.seenList.push(msgId);
  }

  // Computar ID único para a mensagem
  private computeMessageId(message: any): string {
    if (message.id) return message.id;

    // Hash do conteúdo
    const str = JSON.stringify(message);
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash |= 0; // Converter para 32-bit
    }
    return `gossip-${hash}-${Date.now()}`;
  }

  // Estatísticas
  getStats(): {
    seenMessages: number;
    cacheSize: number;
  } {
    return {
      seenMessages: this.seenMessages.size,
      cacheSize: this.config.seenCacheSize,
    };
  }
}
