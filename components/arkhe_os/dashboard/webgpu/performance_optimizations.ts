// arkhe_os/dashboard/webgpu/performance_optimizations.ts

// Stub for CoherenceNode
interface CoherenceNode {
    id: string;
    position: any;
}

class SpatialHash {
    constructor(cellSize: number) {}
    insert(id: string, position: any) {}
}

export class PerformanceOptimizer {
  // Level-of-detail para grafos grandes
  static computeLOD(nodeCount: number, zoomLevel: number): number {
    if (zoomLevel < 0.5) return 0.1;   // 10% dos nós
    if (zoomLevel < 1.0) return 0.3;   // 30% dos nós
    if (zoomLevel < 2.0) return 0.6;   // 60% dos nós
    return 1.0;                         // 100% dos nós
  }

  // Spatial partitioning para raycasting eficiente
  static buildSpatialIndex(nodes: CoherenceNode[], cellSize: number): SpatialHash {
    const hash = new SpatialHash(cellSize);
    for (const node of nodes) {
      hash.insert(node.id, node.position);
    }
    return hash;
  }

  // Throttling de updates de dados
  static throttleUpdates<T>(
    callback: (data: T) => void,
    minInterval: number
  ): (data: T) => void {
    let lastCall = 0;
    let pending: T | null = null;

    return (data: T) => {
      const now = performance.now();
      if (now - lastCall >= minInterval) {
        callback(data);
        lastCall = now;
      } else {
        pending = data;
        setTimeout(() => {
          if (pending) {
            callback(pending);
            pending = null;
            lastCall = performance.now();
          }
        }, minInterval - (now - lastCall));
      }
    };
  }
}
