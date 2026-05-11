import { LFIRGraph, LFIRNode, LFIRNodeType } from '../parser/lfir';

export interface PageRankConfig {
  damping: number;
  maxIterations: number;
  tolerance: number;
  featureWeight: number;
  fileWeight: number;
  registryWeight: number;
}

export class PageRankOrphanMapper {
  private config: PageRankConfig;

  constructor(config: Partial<PageRankConfig> = {}) {
    this.config = {
      damping: 0.85,
      maxIterations: 100,
      tolerance: 1e-6,
      featureWeight: 1.0,
      fileWeight: 0.5,
      registryWeight: 0.3,
      ...config
    };
  }

  computeOrphanRisk(graph: LFIRGraph, componentIds: string[]): Map<string, number> {
    const adjacency = this._buildWeightedAdjacency(graph, componentIds);

    const n = componentIds.length;
    if (n === 0) return new Map();
    let pr = new Array(n).fill(1 / n);

    for (let iter = 0; iter < this.config.maxIterations; iter++) {
      const newPr = new Array(n).fill((1 - this.config.damping) / n);

      for (let i = 0; i < n; i++) {
        const componentId = componentIds[i];
        const inbound = adjacency.inbound.get(componentId) || [];

        for (const [sourceId, weight] of inbound) {
          const sourceIdx = componentIds.indexOf(sourceId);
          if (sourceIdx === -1) continue;

          const outDegree = adjacency.outDegree.get(sourceId) || 1;
          newPr[i] += this.config.damping * weight * pr[sourceIdx] / outDegree;
        }
      }

      const diff = pr.reduce((sum, val, idx) => sum + Math.abs(val - newPr[idx]), 0);
      pr = newPr;
      if (diff < this.config.tolerance) break;
    }

    const maxPr = Math.max(...pr);
    const minPr = Math.min(...pr);
    const riskMap = new Map<string, number>();

    for (let i = 0; i < n; i++) {
      const componentId = componentIds[i];
      const normalizedPr = maxPr === minPr ? 1 : (pr[i] - minPr) / (maxPr - minPr);
      riskMap.set(componentId, 1 - normalizedPr);
    }

    return riskMap;
  }

  private _buildWeightedAdjacency(
    graph: LFIRGraph,
    componentIds: string[]
  ): {
    inbound: Map<string, Array<[string, number]>>,
    outDegree: Map<string, number>
  } {
    const inbound = new Map<string, Array<[string, number]>>();
    const outDegree = new Map<string, number>();

    for (const id of componentIds) {
      inbound.set(id, []);
      outDegree.set(id, 0);
    }

    for (const edge of graph.edges) {
      const source = graph.nodes.find(n => n.id === edge.from);
      const target = graph.nodes.find(n => n.id === edge.to);

      if (!source || !target) continue;

      if (source.type === LFIRNodeType.Module && target.type === LFIRNodeType.Module) {
        if (source.attributes['type'] === 'feature' && target.attributes['type'] === 'component') {
          this._addWeightedEdge(inbound, outDegree, target.id, source.id, this.config.featureWeight);
        }
        else if (source.attributes['type'] === 'component' && target.attributes['type'] === 'component') {
          this._addWeightedEdge(inbound, outDegree, target.id, source.id, 0.7);
        }
      }

      if (source.type === LFIRNodeType.Module && source.attributes['type'] === 'component') {
        if (target.type === LFIRNodeType.Operation && target.attributes['type'] === 'file') {
          this._addWeightedEdge(inbound, outDegree, source.id, target.id, this.config.fileWeight);
        }
        if (target.type === LFIRNodeType.Metadata && target.attributes['type'] === 'registry') {
          this._addWeightedEdge(inbound, outDegree, source.id, target.id, this.config.registryWeight);
        }
      }
    }

    return { inbound, outDegree };
  }

  private _addWeightedEdge(
    inbound: Map<string, Array<[string, number]>>,
    outDegree: Map<string, number>,
    targetId: string,
    sourceId: string,
    weight: number
  ): void {
    if (!inbound.has(targetId)) return;
    const edges = inbound.get(targetId)!;
    edges.push([sourceId, weight]);
    inbound.set(targetId, edges);

    const current = outDegree.get(sourceId) || 0;
    outDegree.set(sourceId, current + weight);
  }
}
