// ═══════════════════════════════════════════════════════════════════
// ARKHE.D.TS — Declarações de tipos para arkhe.js
// Substrato 765-ARKHE-OS-GEOMETRIC-REFACTOR
// ═══════════════════════════════════════════════════════════════════

export const CONSTANTS: {
  readonly PHI: number;
  readonly PSI: number;
  readonly XI: number;
  readonly GHOST_THRESHOLD: number;
  readonly CONVERGENCE_THRESHOLD: number;
  readonly SYNCHRONIZATION_THRESHOLD: number;
  readonly ROOT_ITEMS: number;
  readonly DOMAINS: number;
  readonly DOMAIN_QUANTUM: string;
  readonly DOMAIN_PARSING: string;
  readonly DOMAIN_ENTERPRISE: string;
  readonly DOMAIN_GOVERNANCE: string;
  readonly DOMAIN_CORE: string;
  readonly CROSS_SUBSTRATES: number[];
  readonly K_BASE_DEFAULT: number;
  readonly K_BASE_MAX: number;
  readonly K_BASE_CHAOS: number;
};

export interface DomainConfig {
  name: string;
  phiC?: number;
}

export interface ModuleMetadata {
  substrate?: number;
  phiC?: number;
  theta?: number;
  [key: string]: any;
}

export interface DomainStatus {
  name: string;
  modules: number;
  coherence: number;
  theta: number;
}

export interface PolytopeStatus {
  phiInterop: number;
  phase: string;
  ghostThreshold: number;
  convergenceThreshold: number;
  domains: DomainStatus[];
  vertices: number;
}

export class XiMPolytope {
  constructor(config?: { [domainName: string]: DomainConfig });
  registerModule(domainName: string, moduleName: string, metadata?: ModuleMetadata): boolean;
  calculateInterop(): number;
  status(): PolytopeStatus;
}

export interface HyperedgeData {
  vertices: Int32Array;
  size: number;
  phiC: number;
}

export interface KuramotoHistoryEntry {
  t: number;
  r: number;
}

export class KuramotoHypergraph {
  N: number;
  K: number;
  theta: Float64Array;
  omega: Float64Array;
  hyperedges: HyperedgeData[];
  phiC: Float64Array;

  constructor(N?: number, K?: number);
  addHyperedge(vertices: number[], phiC?: number): void;
  orderParameter(): number;
  step(dt?: number): number;
  simulate(T?: number, dt?: number): KuramotoHistoryEntry[];
}

export interface PatternConfig {
  name: string;
  problems: number[];
}

export interface DSAResult {
  error?: string;
  pattern?: string;
  problem?: number;
  progress?: string;
  theta?: number;
  coherence?: number;
  kP?: number;
  critical?: boolean;
  templateReady?: boolean;
  rDSA?: number;
  alert?: string | null;
}

export interface DSAStatus {
  rDSA: number;
  phase: string;
  ghostThreshold: number;
  convergenceThreshold: number;
  patterns: PatternInfo[];
  strongest: PatternInfo | null;
  weakest: PatternInfo | null;
  templatesDue: PatternInfo[];
}

export interface PatternInfo {
  key: string;
  name: string;
  progress: string;
  theta: number;
  coherence: number;
  kP: number;
  critical: boolean;
  template: boolean;
}

export class DSACoherenceTracker {
  constructor(config?: { patterns?: { [key: string]: PatternConfig } });
  solve(patternKey: string, problemId: number): DSAResult;
  orderParameter(): number;
  status(): DSAStatus;
}

export interface ArkheFullStatus {
  version: string;
  polytope: PolytopeStatus;
  dsa: DSAStatus;
  constants: typeof CONSTANTS;
}

export class Arkhe {
  polytope: XiMPolytope;
  kuramoto: KuramotoHypergraph | null;
  dsaTracker: DSACoherenceTracker;
  version: string;

  constructor();
  initKuramoto(N?: number, K?: number): KuramotoHypergraph;
  status(): ArkheFullStatus;
  command(command: string, args?: any): any;
}
