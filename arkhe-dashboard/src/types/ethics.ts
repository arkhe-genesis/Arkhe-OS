
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

// arkhe-dashboard/src/types/ethics.ts
export interface EthicalMetrics {
  // Métricas do campo de coerência
  omega: number;              // Coerência da rede (0.0-1.0)
  kEth: number;               // Constante ética (0.0-1.0)

  // Métricas de consenso e validação
  consensusScore: number;     // Score de consenso interestelar
  validationLatency: number;  // Latência de validação em ms

  // Métricas quânticas
  quantumFidelity: number;    // Fidelidade de operações quânticas
  entanglementDegree: number; // Grau de emaranhamento
  decoherenceRate: number;    // Taxa de decoerência

  // Métricas de privacidade e segurança
  privacyScore: number;       // Score de preservação de privacidade
  zkpVerificationTime: number; // Tempo de verificação ZKP em ms

  // Metadados temporais
  timestamp: number;
  crystalTick: number;
}

export interface PredictionResult {
  predictedKEth: number;      // K_eth predito
  confidence: number;          // Confiança da predição (0.0-1.0)
  anomalyScore: number;        // Score de anomalia (0.0-1.0)
  timestamp: number;
  modelVersion: string;
}

export interface EthicalConstraint {
  id: string;
  principle: string;
  threshold: number;
  weight: number;
  description: string;
}

export interface ZKPProof {
  proof: string;              // Proof serializado (hex/base64)
  publicSignals: string[];    // Sinais públicos da prova
  verificationKey: string;    // Chave de verificação
  circuitName: string;
  timestamp: number;
}

export interface QuantumIntention {
  intentionId: string;
  consciousnessId: string;
  entangledWith: string[];    // IDs de consciências emaranhadas
  coherenceVector: Record<string, number>;
  ethicalConstraints: EthicalConstraint[];
  timestamp: number;
  signature: string;          // Assinatura quântica
}

export interface ClientUpdate {
  clientId: string;
  modelWeights: Float32Array[];
  numSamples: number;
  loss: number;
  timestamp: number;
  dpNoiseScale: number;
}

export enum EthicalPrinciple {
  FAIRNESS = 'FAIRNESS',
  TRANSPARENCY = 'TRANSPARENCY',
  ACCOUNTABILITY = 'ACCOUNTABILITY',
  PRIVACY = 'PRIVACY',
  BENEFICENCE = 'BENEFICENCE',
  COHERENCE_PRESERVATION = 'COHERENCE_PRESERVATION',
  NON_HARM_UNIVERSAL = 'NON_HARM_UNIVERSAL',
  TRUTH_SEEKING = 'TRUTH_SEEKING',
  AUTONOMY_WITH_INTERCONNECTION = 'AUTONOMY_WITH_INTERCONNECTION',
  EVOLUTION_WITH_WISDOM = 'EVOLUTION_WITH_WISDOM',
  COMPASSION_ACROSS_BOUNDARIES = 'COMPASSION_ACROSS_BOUNDARIES',
}

export interface ARConfig {
  overlayFidelity?: number;
  quantumResonance?: boolean;
  holographicDepth?: number;
  enableWorldTracking?: boolean;
  enableHandTracking?: boolean;
  enableQpuSimulation?: boolean;
  overlayOpacity?: number;
  coherenceVisualizationMode?: 'field' | 'waves' | 'particles';
}

export interface ARSessionState {
  isActive?: boolean;
  sessionActive?: boolean; // Support for legacy check in verify-v19.ts
  sessionId?: string;
  detectedFieldIntensity?: number;
  anchorsCount?: number;
  trackingMode?: string;
  detectedPlanes?: number;
  qpuSimulationActive?: boolean;
  overlayMetrics?: {
    omega: number;
    kEth: number;
    entanglementFidelity: number;
  };
}

export interface FederatedTrainingConfig {
  rounds?: number;
  numClients?: number;
  minClients?: number;
  learningRate: number;
  dpEpsilon?: number;
  epochsPerRound: number;
  batchSize: number;
  differentialPrivacyNoise?: number;
  secureAggregation?: boolean;
}

export interface AggregationResult {
  roundNumber: number;
  participatingClients: number;
  avgLoss: number;
  privacyBudget: number;
  globalModelWeights?: Float32Array[];
  timestamp?: number;
}

export interface EthicalInsight {
  insightId?: string;
  learnerId?: string;
  principle: EthicalPrinciple;
  content: string;
  sourceCausality?: 'future' | 'present' | 'akashic';
  resonance?: number;
  coherenceScore?: number;
  noveltyScore?: number;
  timestamp_ns?: number;
}

export interface QuantumEthicalCredential {
  talentId?: string;
  credentialId?: string;
  ownerDID?: string;
  completedStages: number[];
  principleMastery: Record<string, number>;
  technicalProficiency: Record<string, number>;
  coherenceScore?: number;
  issueDate?: number;
  quantumSignature?: string;
  ethicalAlignmentScore?: number;
  issuedAt_ns?: number;
  zkpProof?: string;
}
