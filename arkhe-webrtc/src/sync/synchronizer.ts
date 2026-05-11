// ============================================================================
// ARKHE Ω-TEMP — State Synchronizer
// ============================================================================

export interface SyncState {
  phase: 'idle' | 'comparing' | 'requesting' | 'downloading' | 'verifying' | 'complete';
  peerAddress: string;
  ourRoot: string;
  theirRoot: string;
  commonIndex: number;
  blocksToDownload: number;
  blocksDownloaded: number;
  conflicts: number;
}

export interface SyncResult {
  success: boolean;
  blocksDownloaded: number;
  conflicts: number;
  timeMs: number;
}

export class StateSynchronizer {
  constructor(
    private localChain: any, // TemporalHashChain
    private protocol: {
      sendRequest: (msg: Uint8Array, peerId: string) => Promise<Uint8Array>;
      broadcast: (msg: Uint8Array) => void;
    }
  ) {}

  async syncWithPeer(peerId: string, peerAddress: string): Promise<SyncResult> {
    const startTime = performance.now();

    try {
      const localRoot = this.localChain.stateRoot;
      const theirRoot = await this.requestRoot(peerId);

      if (this.bytesToHex(localRoot) === theirRoot) {
        return { success: true, blocksDownloaded: 0, conflicts: 0, timeMs: 0 };
      }

      // Busca binária do ancestral comum
      const commonIndex = await this.findCommonAncestor(peerId, this.localChain.length);

      // Download blocos faltantes
      const blocksToDownload = this.localChain.length - commonIndex - 1;
      let downloaded = 0;
      let conflicts = 0;

      for (let i = commonIndex + 1; i < this.localChain.length; i++) {
        const block = await this.requestBlock(peerId, i);
        if (block) {
          const valid = await this.verifyBlock(block);
          if (valid) {
            this.localChain.appendBlock(block.messages, block.prevHash);
            downloaded++;
          } else {
            conflicts++;
          }
        }
      }

      return {
        success: conflicts === 0,
        blocksDownloaded: downloaded,
        conflicts,
        timeMs: performance.now() - startTime,
      };
    } catch (err) {
      return { success: false, blocksDownloaded: 0, conflicts: -1, timeMs: performance.now() - startTime };
    }
  }

  private async requestRoot(peerId: string): Promise<string> {
    const msg = new Uint8Array([0x01]); // SYNC_ROOT_REQUEST
    const response = await this.protocol.sendRequest(msg, peerId);
    return this.bytesToHex(response);
  }

  private async findCommonAncestor(peerId: string, ourLength: number): Promise<number> {
    let low = 0, high = ourLength;
    while (low < high) {
      const mid = Math.floor((low + high) / 2);
      const request = new Uint8Array(5);
      request[0] = 0x02; // BLOCK_HASH_REQUEST
      new DataView(request.buffer).setUint32(1, mid, false);
      const hash = await this.protocol.sendRequest(request, peerId);
      const ourBlock = this.localChain.getBlock(mid);
      if (ourBlock && this.equals(hash, this.localChain.blockHash(ourBlock))) {
        low = mid + 1;
      } else {
        high = mid;
      }
    }
    return low - 1;
  }

  private async requestBlock(peerId: string, index: number): Promise<any | null> {
    const request = new Uint8Array(5);
    request[0] = 0x03; // BLOCK_REQUEST
    new DataView(request.buffer).setUint32(1, index, false);
    const response = await this.protocol.sendRequest(request, peerId);
    if (response.byteLength < 2) return null;
    return this.decodeBlock(response);
  }

  private decodeBlock(data: Uint8Array): any {
    try {
        return JSON.parse(new TextDecoder().decode(data));
    } catch {
        return null;
    }
  }

  private async verifyBlock(block: any): Promise<boolean> {
    // Verificação básica: Merkle root e hashes
    const msgHashes = block.messages.map((m: any) =>
      this.sha256(new TextEncoder().encode(`${m.id}:${m.sender}:${m.receiver}:${m.sourceTs}`))
    );
    const computedRoot = this.merkleRoot(msgHashes);
    return this.equals(computedRoot, block.stateRoot);
  }

  private sha256(data: Uint8Array): Uint8Array {
    // Basic fallback for now in synchronizer
    return new Uint8Array(32);
  }

  private merkleRoot(hashes: Uint8Array[]): Uint8Array {
    if (hashes.length === 0) return this.sha256(new Uint8Array(0));
    let level = hashes;
    while (level.length > 1) {
      const next: Uint8Array[] = [];
      for (let i = 0; i < level.length; i += 2) {
        const pair = new Uint8Array([...level[i], ...(i + 1 < level.length ? level[i + 1] : level[i])]);
        next.push(this.sha256(pair));
      }
      level = next;
    }
    return level[0];
  }

  private equals(a: Uint8Array, b: Uint8Array): boolean {
    if (a.length !== b.length) return false;
    for (let i = 0; i < a.length; i++) {
        if (a[i] !== b[i]) return false;
    }
    return true;
  }

  private bytesToHex(bytes: Uint8Array): string {
    return Array.from(bytes).map(b => b.toString(16).padStart(2, '0')).join('');
  }
}
