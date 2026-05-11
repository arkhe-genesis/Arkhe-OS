// ============================================================================
// ARKHE Ω-TEMP — Mesh Router
// ============================================================================
// Roteamento em mesh usando Dijkstra adaptativo com métricas ARKHE.
// Cada peer mantém uma tabela de roteamento baseada em:
//   - Latência medida (ping/pong)
//   - Score de consenso do peer
//   - Disponibilidade (up/down detection)
//   - Carga do peer (mensagens pendentes)
// ============================================================================

import { Address, RouteResult, PeerInfo } from '../core/types';

interface RouteEntry {
  destination: Address;
  nextHop: Address;
  cost: number;
  hops: number;
  consistency: number;
  lastUpdated: number;
}

interface RouteMetrics {
  latency: number;
  reliability: number;
  load: number;
  consistency: number;
}

export class RoutingTable {
  private routes: Map<Address, RouteEntry> = new Map();
  private metrics: Map<Address, RouteMetrics> = new Map();
  private myAddress: Address;
  private maxHops: number = 16;

  constructor(myAddress: Address) {
    this.myAddress = myAddress;
  }

  // Adicionar peer à tabela
  addPeer(info: PeerInfo): void {
    this.routes.set(info.address, {
      destination: info.address,
      nextHop: info.address,
      cost: this.computeInitialCost(info),
      hops: 1,
      consistency: info.consistencyScore,
      lastUpdated: Date.now(),
    });

    this.metrics.set(info.address, {
      latency: info.latency,
      reliability: 1.0,
      load: 0,
      consistency: info.consistencyScore,
    });
  }

  // Remover peer
  removePeer(address: Address): void {
    this.routes.delete(address);
    this.metrics.delete(address);

    // Remover rotas que passam por este peer
    this.routes.forEach((route, dest) => {
      if (route.nextHop === address) {
        this.routes.delete(dest);
      }
    });
  }

  // Atualizar métricas de um peer
  updateMetrics(address: Address, metrics: Partial<RouteMetrics>): void {
    const existing = this.metrics.get(address);
    if (existing) {
      Object.assign(existing, metrics);

      // Atualizar custo da rota
      const route = this.routes.get(address);
      if (route) {
        route.cost = this.computeRouteCost(address);
        route.consistency = metrics.consistency ?? route.consistency;
        route.lastUpdated = Date.now();
      }
    }
  }

  // Encontrar melhor rota para um destino
  findBestRoute(destination: Address): RouteResult | undefined {
    // Dijkstra simplificado para mesh
    const distances: Map<Address, number> = new Map();
    const previous: Map<Address, Address | null> = new Map();
    const visited: Set<Address> = new Set();
    const peers = Array.from(this.routes.keys());

    // Inicializar distâncias
    peers.forEach(p => distances.set(p, Infinity));
    distances.set(this.myAddress, 0);

    // Nós a visitar
    const unvisited = new Set([this.myAddress, ...peers]);

    while (unvisited.size > 0) {
      // Encontrar nó com menor distância
      let current: Address | null = null;
      let minDist = Infinity;
      unvisited.forEach(node => {
        const d = distances.get(node) ?? Infinity;
        if (d < minDist) {
          minDist = d;
          current = node;
        }
      });

      if (!current || minDist === Infinity) break;
      if (current === destination) break;

      unvisited.delete(current);
      visited.add(current);

      // Relaxar vizinhos
      this.routes.forEach((route, dest) => {
        if (visited.has(dest)) return;
        if (route.nextHop === current || dest === current) {
          const alt = (distances.get(current) ?? Infinity) + route.cost;
          if (alt < (distances.get(dest) ?? Infinity)) {
            distances.set(dest, alt);
            previous.set(dest, current);
          }
        }
      });
    }

    // Reconstruir caminho
    const path: Address[] = [];
    let current: Address | null = destination;
    while (current && current !== this.myAddress) {
      path.unshift(current);
      current = previous.get(current) ?? null;
      if (path.length > this.maxHops) return undefined; // Loop protection
    }
    path.unshift(this.myAddress);

    const totalCost = distances.get(destination) ?? Infinity;
    if (totalCost === Infinity) return undefined;

    // Calcular consenso mínimo ao longo do caminho
    let minConsensus = 1.0;
    for (const addr of path) {
      const m = this.metrics.get(addr);
      if (m) {
        minConsensus = Math.min(minConsensus, m.consistency);
      }
    }

    return {
      path,
      totalCost,
      minConsensus,
      hops: path.length - 1,
      estimatedLatency: totalCost * 10, // Heurística
    };
  }

  // Encontrar múltiplas rotas (para redundância)
  findMultipleRoutes(
    destination: Address,
    count: number = 3
  ): RouteResult[] {
    const routes: RouteResult[] = [];
    const usedPaths = new Set<string>();

    for (let i = 0; i < count; i++) {
      const route = this.findBestRoute(destination);
      if (!route) break;

      const pathKey = route.path.join('→');
      if (usedPaths.has(pathKey)) continue;

      routes.push(route);
      usedPaths.add(pathKey);

      // Penalizar nós usados para encontrar rotas alternativas
      route.path.forEach(addr => {
        const metrics = this.metrics.get(addr);
        if (metrics) {
          metrics.load = Math.min(1.0, metrics.load + 0.1);
        }
      });
    }

    return routes;
  }

  // Roteamento com fator de consenso
  findConsensusAwareRoute(
    source: Address,
    destination: Address,
    minConsensus: number = 0.85
  ): RouteResult | undefined {
    const route = this.findBestRoute(destination);
    if (!route) return undefined;

    // Verificar se o consenso mínimo está satisfeito
    if (route.minConsensus < minConsensus) {
      // Tentar encontrar rota alternativa com melhor consenso
      const alternatives = this.findAlternativeRoutes(
        source, destination, minConsensus
      );

      if (alternatives.length > 0) {
        return alternatives[0]; // Melhor alternativa
      }

      return undefined; // Nenhuma rota com consenso suficiente
    }

    return route;
  }

  private findAlternativeRoutes(
    source: Address,
    destination: Address,
    minConsensus: number
  ): RouteResult[] {
    const alternatives: RouteResult[] = [];

    // Busca em profundidade limitada
    const dfs = (
      current: Address,
      path: Address[],
      visited: Set<Address>,
      cost: number
    ) => {
      if (current === destination) {
        const minCons = path.reduce((min, addr) => {
          const m = this.metrics.get(addr);
          return Math.min(min, m?.consistency ?? 0);
        }, 1.0);

        if (minCons >= minConsensus) {
          alternatives.push({
            path: [...path],
            totalCost: cost,
            minConsensus: minCons,
            hops: path.length - 1,
            estimatedLatency: cost * 10,
          });
        }
        return;
      }

      if (path.length > this.maxHops) return;

      this.routes.forEach((route, dest) => {
        if (!visited.has(dest) && route.nextHop === current) {
          const metrics = this.metrics.get(dest);
          if (metrics && metrics.consistency >= minConsensus * 0.8) {
            visited.add(dest);
            dfs(dest, [...path, dest], visited, cost + route.cost);
            visited.delete(dest);
          }
        }
      });
    };

    dfs(source, [source], new Set([source]), 0);

    // Ordenar por custo
    alternatives.sort((a, b) => a.totalCost - b.totalCost);

    return alternatives;
  }

  // Custo baseado em múltiplos fatores
  private computeRouteCost(address: Address): number {
    const metrics = this.metrics.get(address);
    if (!metrics) return Infinity;

    // Custo = latência + penalidade de carga + inversa do consenso
    const latencyFactor = metrics.latency / 1000; // Normalizado
    const loadFactor = metrics.load * 10;
    const consensusFactor = metrics.consistency < 0.5
      ? 100 // Penalidade severa para baixo consenso
      : 1 / (metrics.consistency + 0.01);

    return latencyFactor + loadFactor + consensusFactor;
  }

  private computeInitialCost(info: PeerInfo): number {
    return (
      (info.latency / 1000) + // Latência em segundos
      (1 / (info.consistencyScore + 0.01)) // Incentivar alto consenso
    );
  }

  getEntries(): Map<Address, RouteEntry> {
    return this.routes;
  }

  size(): number {
    return this.routes.size;
  }
}
