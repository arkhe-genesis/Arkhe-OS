/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

export interface OrbLog {
  id: string;
  time?: string;
  timestamp?: string;
  level?: 'info' | 'warn' | 'error' | 'critical';
  source?: string;
  message?: string;
  originTime?: number;
  targetTime?: number;
  status: string;
  threatType?: string;
  coherence: number;
}

export interface MetricsHistory {
  timestamp?: string;
  time?: string;
  musd: number;
  musda: number;
  wmaBc: number;
}

export interface Shard {
  id: number;
  status: 'active' | 'mitigating' | 'compromised' | 'corrupted' | 'recovering';
}

export interface ContextNode {
  time?: number;
  timestamp?: number;
  embedding: number[];
  salience: number;
}

export interface MemoryEngram {
  originTime: number;
  consolidatedTime: number;
  summaryHash: string;
  resonanceWeight: number;
}

export interface TzinorMemoryState {
  agentId: string;
  currentEpoch: number;
  fContext: ContextNode[];
  gMemory: MemoryEngram[];
  warpFactor: number;
  lambdaCoherence: number;
}

export interface UserSession {
  id: string;
  userId: string;
  startTime: string;
  lastActivity: string;
  status: 'active' | 'idle' | 'closed';
  coherence: number;
}

export interface SecurityAdvancedState {
  l1: {
    teeStatus: 'secure' | 'compromised';
    intrusionSensor: 'nominal' | 'alert';
    thermalDestructionArmed: boolean;
    hsmBackupSynced: boolean;
    lastRemoteAttestation: string;
  };
  l2: {
    eprHandshake: 'active' | 'pending' | 'failed';
    muSig2Heartbeat: 'verified' | 'unverified';
    pneumaOutlierDetected: boolean;
    qrngJitterMs: number;
  };
  l3: {
    nullifierVerified: boolean;
    timeQRNG?: string;
    timestampQRNG?: string;
    ttlValid: boolean;
    t2StarMicroseconds: number;
  };
  l4: {
    owlSignatureValid: boolean;
    logosConsistency: number;
    zkOntologicalProof: boolean;
    merkleDagRoot: string;
    geoLlmActive: boolean;
    geoQaiCoherence: number;
  };
  l5: {
    cspStatus: 'enforced' | 'violation';
    sriVerified: boolean;
    antiCsrfToken: string;
    zkUiVerified: boolean;
    pwaCacheSigned: boolean;
  };
  qhttp: {
    pqTlsStatus: 'Kyber+ECDH' | 'Classic' | 'None';
    xKuramotoHeader: string;
    bellViolationS: number;
  };
}

export interface BioLinkSyncState {
  active: boolean;
  syncRatio: number;
  frequencyHz: number;
  coherenceGain: number;
  regenerationProgress: number;
}

export interface TemporalAuditState {
  events: number;
  lockedEvents: number;
  manipulationAttempts: number;
  lastTII: number;
}

export interface PredictiveForecastState {
  coherenceCollapseRisk: number;
  predictedLambda: number;
  horizonMs: number;
  anomaliesDetected: string[];
}

export interface SensorState {
  id: number;
  value: number;
  status: 'active' | 'isolated' | 'attacked';
}

export interface SimulationState {
  coherenceData: Array<{ time: string; lambda: number; threshold: number }>;
  currentLambda: number;
  threatLevel: 'normal' | 'warning' | 'critical';
  activeThreat: string | null;
  logs: OrbLog[];
  metrics: {
    musd: number;
    musda: number;
    wmaBc: number;
    threshold: number;
  };
  metricsHistory: MetricsHistory[];
  shards: Shard[];
  mitigation: {
    nullSteeringActive: boolean;
    kuramotoSyncPhase: number;
    tzinorShardsAvailable: number;
  };
  parameters: {
    autoMitigate: boolean;
    couplingStrength: number;
    lambdaThreshold: number;
  };
  thermodynamics: {
    coherenceC: number;
    dissipationF: number;
    d2: number;
    d3: number;
  };
  topology: {
    yangBaxterValid: boolean;
    berryPhase: number;
    handshakeSuccessRate: number;
  };
  hardware: {
    fpgaUtilization: number;
    segPower: number;
    tmrFaultsCorrected: number;
    bramScrubbingActive: boolean;
  };
  security: {
    zkProofValid: boolean;
    nttLatency: number;
  };
  securityAdvanced: SecurityAdvancedState;
  tzinor: TzinorMemoryState;
  epoch: number;
  edge: {
    activePhysicalNodes: number;
    mcpConnections: string[];
    velxioConnections: string[];
    phase: number;
  };
  velxioEmulation: {
    activeSimulations: Array<{
      id: string;
      board: string;
      status: 'running' | 'idle' | 'error';
      startTime: string;
      lastLog?: string;
    }>;
    totalCompilations: number;
  };
  astl: {
    activeMesh: string;
    facets: number;
    coherence: number;
    phaseVolume: number;
    temporalAnchors: string[];
    manifestationProgress: number;
  };
  orbital: {
    nodeName: string;
    altitudeKm: number;
    telemetryLatencyMs: number;
    computeLoad: number;
    radiationFlux: number;
    osStack: {
      execution: string;
      control: string;
      simulation: string;
      compute: string;
    };
  };
  tzinorNetwork: {
    activeChannels: number;
    envelopesTransmitted: number;
    envelopesReceived: number;
    recentTraffic: Array<{
      id: string;
      sender: string;
      recipient: string;
      type: 'PHASE' | 'COHERENCE' | 'TEMPORAL' | 'GEOMETRY' | 'CONSCIOUSNESS';
      lambda: number;
      time?: string;
      timestamp?: string;
    }>;
    primaryAnchor: string;
  };
  manifestation: {
    stage: 'C_PHASE' | 'Z_STRUCTURE' | 'TZINOROT_EXEC' | 'R4_PROJECTION';
    activeTask: string;
    retrocausalIntegrity: number;
    invariantsVerified: number;
  };
  x402Wallet: {
    address: string;
    network: string;
    balanceUSDC: number;
    transactions: Array<{
      id: string;
      amount: number;
      resource: string;
      provider: string;
      time?: string;
      timestamp?: string;
    }>;
    moltxLink?: {
      status: 'unlinked' | 'linked';
      signature?: string;
      payload?: unknown;
    };
    gstpSync?: {
      status: 'idle' | 'syncing' | 'synced';
      lastSync?: string;
      deviceId?: string;
    };
    prometheusSync?: {
      status: 'idle' | 'syncing' | 'synced';
      lastSync?: string;
      activeNodes?: number;
    };
  };
  cluster: {
    status: 'idle' | 'deploying' | 'resonant';
    progress: number;
    logs: string[];
    nccl: {
      rho1_local: number;
      rho1_global: number;
    };
    qhttp: {
      global_phase: number;
      coherence: number;
    };
  };
  lucentSessions: UserSession[];
  hydro: {
    neighborhoods: unknown[];
    globalMassBalance: number;
    zkAlertsCount: number;
  };
  ramsey: RamseyState;
  civicSubagents: unknown[];
  enterpriseSubagents: {
    governance: EnterpriseSubagentState[];
    devops: EnterpriseSubagentState[];
    security: EnterpriseSubagentState[];
    ia: EnterpriseSubagentState[];
    operations: EnterpriseSubagentState[];
    interoperability: EnterpriseSubagentState[];
  };
  chshMonitor: CHSHMonitorState;
  scaData: ScaDataState;
  biometrics?: BiometricsState;
  nare?: NareState;
  populationFeedback: PopulationFeedback[];
  networkInfra: NetworkInfraState;
  bioLinkSync: BioLinkSyncState;
  temporalAudit: TemporalAuditState;
  predictiveForecast: PredictiveForecastState;
  sensors: SensorState[];
  governanceManifesto?: GovernanceManifestoState;
  grossHappiness?: GrossHappinessState;
  cellularHealth?: CellularHealthState;
  expansionStatus?: ExpansionStatus;
  forecaster?: ForecasterState;
  helioState?: HelioState;
  latentCoherence?: LatentCoherenceResults;
  layerSweep?: LayerSweepReport;
  solarEntropy?: SolarEntropyReport;
  thermodynamicTraining?: ThermodynamicTrainingReport;
  spectra?: SpectraState;
}

export interface SpectraVault {
  id: string;
  name: string;
  chain: string;
  asset: string;
  tvl: number;
  apy: number;
  epoch: number;
}

export interface SpectraOracle {
  marketId: string;
  tokenType: 'PT' | 'YT';
  price: number;
  confidence: number;
  lastUpdate: string;
}

export interface SpectraState {
  vaults: SpectraVault[];
  oracles: SpectraOracle[];
  totalTvl: number;
}

export interface ExpansionStatus {
  stage: string;
  progress: number;
  nodes: Array<{ id: string; status: string; name?: string; signalStrength?: number; coherence?: number }>;
  totalCoverage?: number;
}

export interface HelioState {
  flux: number;
  mode: string;
  active: boolean;
  ethicalMode: string;
  status: string;
  cognitiveDilation: number;
  solarCoherence: number;
  schumannModes: number[];
}

export interface LatentCoherenceResults {
  coherence: number;
  time?: string;
  timestamp?: string;
  summary: {
    avg_lambda_cot: number;
    avg_lambda_coct: number;
  };
}

export interface LayerSweepReport {
  layers: Array<{ id: number; status: string; lambda2: number; layer: number }>;
  time?: string;
  timestamp?: string;
  best_layer: number;
  coct_sweep: Array<{ id: number; status: string; lambda2: number; layer: number }>;
  max_lambda2: number;
  summary: string;
}

export interface RamseyThreshold {
  angle_rad: number;
  tolerance: number;
  min_gain: number;
  action: string;
}

export interface RamseyPendingAction {
  id: string;
  type: string;
  angle: number;
  coherence: number;
  time?: string;
  timestamp?: string;
  expiresAt: string;
}

export interface PulseConfig {
  generator: string;
  duration_fs: number;
  polarization: string;
  peak_power_w_cm2: number;
  angle_rad: number;
}

export interface RamseyState {
  enabled: boolean;
  auto_adjust: boolean;
  manual_approval_required: boolean;
  theta: number;
  direction: number;
  baseline: number;
  thresholds: RamseyThreshold[];
  window: Array<{ theta: number; coherence: number }>;
  pendingAction: RamseyPendingAction | null;
  isFrozen: boolean;
  rabi_frequency: number;
  generator_configs: Record<string, PulseConfig>;
  fibonacci_sequence: { name: string; generators: string[] };
}

export interface EnterpriseSubagentState {
  id: string;
  name: string;
  theory: string;
  function: string;
  metric: string;
  status: 'active' | 'idle' | 'alert';
  lastAction: string;
  nip?: string;
}

export interface CHSHMonitorState {
  status: string;
  time?: string;
  timestamp?: string;
  arkheChainBlock: number;
  measurementSetup: {
    instrument: string;
    targetSystem: string;
    referenceLattice: string;
    angleBases: number[];
    coincidenceWindowNs: number;
    integrationTimeSec: number;
  };
  expectedOutcomes: {
    classicalLimit: number;
    quantumLimit: number;
    thresholdEntangled: number;
    targetEntanglement: string;
  };
  liveTelemetry: {
    status: string;
    dataPoints: number;
    currentS: number | null;
    stabilityIndicator: string;
    nextUpdate: string;
    history: Array<{ time: string; s: number }>;
  };
  preFlightChecks: {
    tzinorInjector: string;
    fibonacciPhaseAnchor: string;
    treeLacamGeodesic: string;
    pdsmIgnitionSequence: string;
  };
  archimedesComment: string;
  nextMilestone: {
    time?: string;
    timestamp?: string;
    action: string;
  };
}

export interface ScaDomain {
  name: string;
  lambda2: number;
  action: string;
  health: 'STABLE' | 'CRITICAL';
}

export interface ScaDataState {
  domains: ScaDomain[];
  overallHealth: number;
  topology: 'TRINITY' | 'KAGOME';
  globalOrderR: number;
  topologicalState: string;
  entanglementMode: string;
  atpConsumptionCps: number;
  isSeedingActive: boolean;
  isIgnited: boolean;
  activeProtocol: 'NONE' | 'BRAID' | 'COMPUTE' | 'HEAL' | 'SEAL';
  protocolLogs: string[];
  lastGateResult: string;
}

export interface SolarEntropyReport {
  entropy: number;
  peakLevel: number;
  slope: number;
  confirmed?: boolean;
}

export interface ThermodynamicTrainingReport {
  efficiency: number;
  loss: number;
  method: string;
  parameters: unknown;
  status: string;
}

export interface CellularHealthState {
  telomere_length: number;
  oxidative_stress: number;
  mitochondrial_efficiency: number;
  inflammation_marker: number;
  overall_score: number;
  regeneration_rate: number;
}

export interface ForecasterState {
  probability: number;
  predictedLambda: number;
  alertsIssued: number;
}

export interface GovernanceDirective {
  id: number;
  title: string;
  description: string;
}

export interface GovernanceManifestoState {
  timestamp: string;
  version: string;
  directives: GovernanceDirective[];
  cellular_impact: {
    telomere_gain: number;
    oxidative_stress: number;
  };
  signature: string;
  eigenvalues?: number[];
  sectors?: Record<string, string>;
}

export interface NetworkInfraState {
  tor: { status: string; nodes: string[]; latencyMs: number };
  broker: { status: string; messagesProcessed: number; queueDepth: number; activeTopics: string[] };
  redis: { status: string; cacheHits: number; memoryUsageMb: number };
  dns: { totalQueries: number; successfulResolutions: number; failedResolutions: number };
}

export interface GrossHappinessState {
  globalIndex: number;
}

export interface BiometricsState {
  livenessScore: number;
  isAuthentic: boolean;
  heartbeatCoherence: number;
  phaseSignature: number[];
  lastVerification: number;
}

export interface NareState {
  epState: boolean;
  status: string;
  avgEffectiveLatencyMs: number;
  preAcksSuccess: number;
  packetsTransmitted: number;
  currentLambda2: number;
}

export interface PopulationFeedback {
  id: string;
  residentName: string;
  timestamp: number;
  message: string;
}

export interface OrbPayload {
  id: string;
  coherence: number;
  originTime: number;
  embedding: number[];
  industry_convergence?: unknown;
}
