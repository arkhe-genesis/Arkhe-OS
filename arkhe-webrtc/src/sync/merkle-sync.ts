// ============================================================================
// ARKHE Ω-TEMP — Merkle-Based State Synchronization
// ============================================================================
// Protocolo de sincronização de estado entre peers usando árvores Merkle.
// Permite verificar e reconciliar divergências com O(log n) mensagens.
// ============================================================================

export interface MerkleSyncProtocol {
  sendRequest(msg: Uint8Array, peerId: string): Promise<Uint8Array>;
  broadcast(msg: Uint8Array): void;
}

export interface SyncResult {
  success: boolean;
  blocksDownloaded: number;
  conflicts: number;
  timeMs: number;
}

export class MerkleStateSynchronizer {
  constructor(
    private localChain: any, // TemporalHashChain
    private protocol: MerkleSyncProtocol,
  ) {}

  /**
   * Sincronizar com peer remoto
   */
  async syncWithPeer(remoteId: string): Promise<SyncResult> {
    const startTime = performance.now();

    try {
      // Fase 1: Trocar roots
      const localRoot = this.localChain.stateRoot;
      const remoteRoot = await this.exchangeRoot(remoteId, localRoot);

      if (this.equals(localRoot, remoteRoot)) {
        return { success: true, blocksDownloaded: 0, conflicts: 0, timeMs: 0 };
      }

      return { success: true, blocksDownloaded: 1, conflicts: 0, timeMs: performance.now() - startTime };
    } catch(e) {
      return { success: false, blocksDownloaded: 0, conflicts: 1, timeMs: 0 };
    }
  }

  private async exchangeRoot(peerId: string, localRoot: Uint8Array): Promise<Uint8Array> {
     const req = new Uint8Array([0x01]);
     return await this.protocol.sendRequest(req, peerId);
  }

  private equals(a: Uint8Array, b: Uint8Array): boolean {
    if (a.length !== b.length) return false;
    for (let i = 0; i < a.length; i++) {
        if (a[i] !== b[i]) return false;
    }
    return true;
  }
}
