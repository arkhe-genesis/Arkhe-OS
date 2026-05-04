/**
 * arkhe-dashboard/src/types/api.ts
 * Shared API types for Arkhe PoC SaaS.
 */

export interface Tenant {
  id: string;
  name: string;
  api_key: string;
  created_at: number;
}

export interface NetworkSummary {
  id: string;
  tenant_id: string;
  name: string;
  target_epsilon: number[];
  sigma: number[];
  consensus_threshold: number;
  odysseus_multiplier: number;
  created_at: number;
}

export interface VertexInfo {
  id: string;
  network_id: string;
  did: string;
  stake_value: number;
  registered_at: number;
}

export interface TelemetryData {
  omega: number;
  kEth: number;
  consensusScore: number;
  validationLatency: number;
  quantumFidelity: number;
  entanglementDegree: number;
  decoherenceRate: number;
  privacyScore: number;
  zkpVerificationTime: number;
  timestamp: number;
  crystalTick: number;
  networkId?: string;
  networkName?: string;
  vertexCount?: number;
}

export interface CoherenceMetrics {
  consensusScore: number;
  totalVertices: number;
  activeVertices: number;
  forkCount: number;
  avgStakeValue: number;
}
