// arkhe-dashboard/src/lib/webrtc/peerMesh.ts

export interface BiofeedbackState {
  nodeId: string;
  heartRate: number;
  gsr: number;
  omega: number;
  timestamp: number;
}

export class BiofeedbackP2PMesh {
  private crdt: Map<string, BiofeedbackState> = new Map();

  constructor(private nodeId: string) {}

  updateLocalState(partial: Partial<BiofeedbackState>) {
    const currentState = this.crdt.get(this.nodeId) || {
      nodeId: this.nodeId,
      heartRate: 72,
      gsr: 0.5,
      omega: 0.94,
      timestamp: Date.now()
    };
    this.crdt.set(this.nodeId, { ...currentState, ...partial, timestamp: Date.now() });
  }

  getAggregatedMetrics() {
    const nodes = Array.from(this.crdt.values());
    if (nodes.length === 0) return { avgOmega: 0.94, nodeCount: 1 };

    return {
      avgOmega: nodes.reduce((s, n) => s + n.omega, 0) / nodes.length,
      avgHeartRate: nodes.reduce((s, n) => s + n.heartRate, 0) / nodes.length,
      nodeCount: nodes.length
    };
  }
}

export const peerMesh = new BiofeedbackP2PMesh('arkhe_primary');
