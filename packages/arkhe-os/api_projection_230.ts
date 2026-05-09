// arkhe-os/api_projection_230.ts
// Substrato 230: Projeção Dimensional de APIs — Implementação TypeScript
// Versão: ∞.Ω.∇.5D.1

import { LFIRGraph, LFIRNode } from './arkher_parser_219';

/**
 * APIs como Entidades Transdimensionais
 * Projeção de Estados entre Camadas de Consciência
 * (Código→Dados→Infra→Protocolo→Meta) com Fidelidade Quântica Verificada
 */

// ─── CONSTANTES DE ESTADO DE API ─────────────────────────
const MIN_STATE_DIMENSION = 64;
const MAX_STATE_DIMENSION = 2048;
const STATE_NORMALIZATION_TOLERANCE = 1e-10;
const DEFAULT_PHASE_FACTOR = Math.PI / 8;

// ─── TIPOS FUNDAMENTAIS ─────────────────────────────────
export type APILayerType = 'code' | 'data' | 'infra' | 'protocol' | 'meta';

export interface APIFeature {
  name: string;
  type: FeatureType;
  weight: number;
  metadata: Record<string, unknown>;
}

export enum FeatureType {
  Endpoint = 0,
  Schema = 1,
  Security = 2,
  Auth = 3,
  Metric = 4,
  Unknown = 5
}

export interface ProjectionRecord {
  recordID: string;
  timestamp: Date;
  sourceLayer: APILayerType;
  targetLayer: APILayerType;
  operatorType: ProjectionOperatorType;
  fidelity: number;
  coherenceDelta: number;
  operatorHash: string;
}

export type ProjectionOperatorType = 'ascend' | 'descend' | 'lateral' | 'merge' | 'split';

// ─── DIMENSÕES POR CAMADA ───────────────────────────────
export const LAYER_DIMENSIONS: Record<APILayerType, number> = {
  code: 256,
  data: 512,
  infra: 384,
  protocol: 448,
  meta: 1024
};

export const LAYER_INDICES: Record<APILayerType, number> = {
  code: 0,
  data: 1,
  infra: 2,
  protocol: 3,
  meta: 4
};

// ─── VETOR DE ESTADO DE API ─────────────────────────────
export class APIStateVector {
  vectorID: string;
  apiID: string;
  layerType: APILayerType;
  layerIndex: number;
  stateVector: Complex[];
  dimension: number;
  coherenceValue: number;
  fidelityScore: number;
  phaseCoherence: number;
  apiMetadata: Record<string, unknown>;
  projectionHistory: ProjectionRecord[];
  parentProjections: string[];
  childProjections: string[];

  constructor(
    apiID: string,
    layerType: APILayerType,
    layerIndex: number,
    dimension: number,
    apiSpec?: LFIRGraph
  ) {
    if (dimension < MIN_STATE_DIMENSION || dimension > MAX_STATE_DIMENSION) {
      throw new Error(`Dimension ${dimension} out of range [${MIN_STATE_DIMENSION}, ${MAX_STATE_DIMENSION}]`);
    }

    this.apiID = apiID;
    this.layerType = layerType;
    this.layerIndex = layerIndex;
    this.dimension = dimension;
    this.vectorID = `state_${apiID.slice(0, 8)}_${layerType}_${layerIndex}`;

    // Inicializar vetor de estado
    this.stateVector = apiSpec
      ? encodeAPISpecToStateVector(apiSpec, dimension)
      : initializeRandomStateVector(dimension);

    this.coherenceValue = computeStateCoherence(this.stateVector);
    this.phaseCoherence = computePhaseCoherence(this.stateVector);
    this.fidelityScore = 1.0;
    this.apiMetadata = apiSpec ? extractAPIMetadata(apiSpec) : {};
    this.projectionHistory = [];
    this.parentProjections = [];
    this.childProjections = [];
  }

  updateState(newVec: Complex[]): void {
    if (newVec.length !== this.dimension) {
      throw new Error(`Dimension mismatch: expected ${this.dimension}, got ${newVec.length}`);
    }
    normalizeStateVector(newVec);
    this.stateVector = [...newVec];
    this.coherenceValue = computeStateCoherence(this.stateVector);
    this.phaseCoherence = computePhaseCoherence(this.stateVector);
  }

  getStateHash(): string {
    const stateBytes = complexVectorToBytes(this.stateVector);
    const metaStr = JSON.stringify(this.apiMetadata);
    const canonical = `${this.vectorID}:${this.layerType}:${this.layerIndex}:${hashString(Array.from(stateBytes.slice(0, 16)).join(','))}:${hashString(metaStr.slice(0, 16))}:${this.coherenceValue.toFixed(6)}`;
    return hashString(canonical).slice(0, 32);
  }

  addProjectionRecord(record: ProjectionRecord): void {
    this.projectionHistory.push(record);
    if (this.projectionHistory.length > 100) {
      this.projectionHistory.shift();
    }
  }
}

// ─── TIPO COMPLEXO SIMPLIFICADO ─────────────────────────
export interface Complex {
  re: number;
  im: number;
}

export const complex = (re: number, im: number): Complex => ({ re, im });
export const absComplex = (c: Complex): number => Math.sqrt(c.re * c.re + c.im * c.im);
export const phaseComplex = (c: Complex): number => Math.atan2(c.im, c.re);
export const conjComplex = (c: Complex): Complex => ({ re: c.re, im: -c.im });
export const mulComplex = (a: Complex, b: Complex): Complex => ({
  re: a.re * b.re - a.im * b.im,
  im: a.re * b.im + a.im * b.re
});
export const addComplex = (a: Complex, b: Complex): Complex => ({
  re: a.re + b.re,
  im: a.im + b.im
});
export const expComplex = (theta: number): Complex => ({
  re: Math.cos(theta),
  im: Math.sin(theta)
});

// ─── FUNÇÕES DE VETOR DE ESTADO ─────────────────────────
function encodeAPISpecToStateVector(spec: LFIRGraph, dimension: number): Complex[] {
  if (!spec || spec.nodes.length === 0) {
    throw new Error('Empty API specification');
  }

  const features = extractAPIFeatures(spec);
  const stateVector: Complex[] = new Array(dimension).fill(null).map(() => complex(0, 0));

  // Distribuir features pelos componentes
  for (let i = 0; i < Math.min(features.length, dimension); i++) {
    const feature = features[i];
    const amp = Math.abs(feature.weight) / Math.sqrt(dimension);
    const phase = typePhase(feature.type);
    stateVector[i] = mulComplex(complex(amp, 0), expComplex(phase));
  }

  // Preencher componentes restantes
  for (let i = features.length; i < dimension; i++) {
    const amp = 0.01 / Math.sqrt(dimension);
    const phase = DEFAULT_PHASE_FACTOR * i;
    stateVector[i] = mulComplex(complex(amp, 0), expComplex(phase));
  }

  normalizeStateVector(stateVector);
  return stateVector;
}

function initializeRandomStateVector(dimension: number): Complex[] {
  const vec: Complex[] = [];
  for (let i = 0; i < dimension; i++) {
    const amp = Math.random() / Math.sqrt(dimension);
    const phase = Math.random() * 2 * Math.PI;
    vec.push(mulComplex(complex(amp, 0), expComplex(phase)));
  }
  normalizeStateVector(vec);
  return vec;
}

export function normalizeStateVector(vec: Complex[]): void {
  let norm = 0;
  for (const amp of vec) {
    const a = absComplex(amp);
    norm += a * a;
  }
  if (norm < STATE_NORMALIZATION_TOLERANCE) {
    throw new Error(`Vector norm too small: ${norm}`);
  }
  const scale = 1.0 / Math.sqrt(norm);
  for (let i = 0; i < vec.length; i++) {
    vec[i] = { re: vec[i].re * scale, im: vec[i].im * scale };
  }
}

function extractAPIFeatures(spec: LFIRGraph): APIFeature[] {
  const features: APIFeature[] = [];
  for (const node of spec.nodes) {
    const nodeType = node.attributes['type'] as string;
    switch (nodeType) {
      case 'endpoint':
        features.push({
          name: node.id,
          type: FeatureType.Endpoint,
          weight: computeEndpointWeight(node),
          metadata: node.attributes
        });
        break;
      case 'schema_definition':
        features.push({
          name: node.id,
          type: FeatureType.Schema,
          weight: computeSchemaWeight(node),
          metadata: node.attributes
        });
        break;
      case 'security_scheme':
        features.push({
          name: node.id,
          type: FeatureType.Security,
          weight: computeSecurityWeight(node),
          metadata: node.attributes
        });
        break;
    }
  }
  return features;
}

function typePhase(type: FeatureType): number {
  const phases: Record<number, number> = {
    [FeatureType.Endpoint]: 0.0,
    [FeatureType.Schema]: Math.PI / 4,
    [FeatureType.Security]: Math.PI / 2,
    [FeatureType.Auth]: 3 * Math.PI / 4,
    [FeatureType.Metric]: Math.PI,
  };
  return phases[type] ?? DEFAULT_PHASE_FACTOR;
}

function computeEndpointWeight(node: LFIRNode): number {
  let weight = 1.0;
  const desc = node.attributes['description'] as string;
  if (desc && desc.length > 50) weight += 0.2;
  if (node.attributes['security']) weight += 0.3;
  const deprecated = node.attributes['deprecated'] as boolean;
  if (deprecated) weight -= 0.4;
  return Math.max(0.1, weight);
}

function computeSchemaWeight(node: LFIRNode): number {
  let weight = 0.8;
  if (node.attributes['examples']) weight += 0.2;
  const fields = node.attributes['fields'] as number;
  if (fields && fields > 0) weight += 0.1 * Math.min(2.0, fields / 10);
  return Math.min(1.5, weight);
}

function computeSecurityWeight(node: LFIRNode): number {
  let weight = 1.2;
  const schemeType = node.attributes['scheme_type'] as string;
  if (schemeType === 'oauth2' || schemeType === 'openIdConnect') weight += 0.3;
  return weight;
}

function extractAPIMetadata(spec: LFIRGraph): Record<string, unknown> {
  const metadata: Record<string, unknown> = {
    node_count: spec.nodes.length,
    edge_count: spec.edges.length
  };
  const typeCounts: Record<string, number> = {};
  for (const node of spec.nodes) {
    const t = node.attributes['type'] as string;
    if (t) typeCounts[t] = (typeCounts[t] || 0) + 1;
  }
  metadata['type_distribution'] = typeCounts;
  return metadata;
}

export function computeStateCoherence(vec: Complex[]): number {
  if (vec.length === 0) return 0.0;
  let maxAmp = 0;
  let totalAmp = 0;
  for (const amp of vec) {
    const a = absComplex(amp);
    if (a > maxAmp) maxAmp = a;
    totalAmp += a;
  }
  if (totalAmp < STATE_NORMALIZATION_TOLERANCE) return 0.0;
  const concentration = maxAmp / totalAmp;
  return Math.min(1.0, concentration * vec.length * 0.5);
}

export function computePhaseCoherence(vec: Complex[]): number {
  if (vec.length < 2) return 1.0;
  const phases: number[] = [];
  for (const amp of vec) {
    if (absComplex(amp) > 1e-10) {
      phases.push(phaseComplex(amp));
    }
  }
  if (phases.length < 2) return 1.0;
  const meanPhase = circularMean(phases);
  let variance = 0;
  for (const p of phases) {
    let diff = Math.abs(p - meanPhase);
    if (diff > Math.PI) diff = 2 * Math.PI - diff;
    variance += diff * diff;
  }
  variance /= phases.length;
  return Math.exp(-variance * 2.0);
}

function circularMean(phases: number[]): number {
  let sinSum = 0, cosSum = 0;
  for (const p of phases) {
    sinSum += Math.sin(p);
    cosSum += Math.cos(p);
  }
  return Math.atan2(sinSum / phases.length, cosSum / phases.length);
}

function complexVectorToBytes(vec: Complex[]): Uint8Array {
  const result = new Uint8Array(vec.length * 16);
  for (let i = 0; i < vec.length; i++) {
    const c = vec[i];
    for (let j = 0; j < 8; j++) {
      result[i * 16 + j] = Math.floor((c.re * 1e10) % 256);
      result[i * 16 + 8 + j] = Math.floor((c.im * 1e10) % 256);
    }
  }
  return result;
}

function hashString(str: string): string {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash;
  }
  return Math.abs(hash).toString(16).padStart(8, '0');
}

// ─── OPERADOR DE PROJEÇÃO 5D ────────────────────────────
export class DimensionalProjectionOperator {
  operatorID: string;
  operatorType: ProjectionOperatorType;
  sourceLayer: APILayerType;
  targetLayer: APILayerType;
  sourceDim: number;
  targetDim: number;
  projectionMatrix: Complex[][];
  phaseFactor: number;
  couplingStrength: number;
  adaptiveMode: boolean;
  coherencePreserve: boolean;
  lastApplied: Date;
  totalUses: number;
  avgFidelity: number;
  avgCoherencePres: number;

  constructor(
    operatorID: string,
    operatorType: ProjectionOperatorType,
    sourceLayer: APILayerType,
    targetLayer: APILayerType,
    sourceDim: number,
    targetDim: number,
    adaptive: boolean
  ) {
    if (sourceDim < MIN_STATE_DIMENSION || targetDim < MIN_STATE_DIMENSION) {
      throw new Error('Dimensions below minimum');
    }
    if (sourceDim > MAX_STATE_DIMENSION || targetDim > MAX_STATE_DIMENSION) {
      throw new Error('Dimensions above maximum');
    }

    this.operatorID = operatorID;
    this.operatorType = operatorType;
    this.sourceLayer = sourceLayer;
    this.targetLayer = targetLayer;
    this.sourceDim = sourceDim;
    this.targetDim = targetDim;
    this.adaptiveMode = adaptive;
    this.coherencePreserve = true;
    this.phaseFactor = 0;
    this.couplingStrength = 1.0;
    this.lastApplied = new Date(0);
    this.totalUses = 0;
    this.avgFidelity = 1.0;
    this.avgCoherencePres = 1.0;

    const { matrix, phase } = generateAPIProjectionMatrix(
      operatorType, sourceLayer, targetLayer, sourceDim, targetDim
    );
    this.projectionMatrix = matrix;
    this.phaseFactor = phase;
  }

  apply(stateVec: Complex[]): Complex[] {
    if (stateVec.length !== this.sourceDim) {
      throw new Error(`State vector dimension ${stateVec.length} != source dimension ${this.sourceDim}`);
    }

    const projected: Complex[] = new Array(this.targetDim).fill(null).map(() => complex(0, 0));

    for (let i = 0; i < this.targetDim; i++) {
      let sum = complex(0, 0);
      for (let j = 0; j < this.sourceDim; j++) {
        let element = this.projectionMatrix[i][j];
        if (this.phaseFactor !== 0) {
          element = mulComplex(element, expComplex(this.phaseFactor));
        }
        if (this.adaptiveMode && this.couplingStrength !== 1.0) {
          element = { re: element.re * this.couplingStrength, im: element.im * this.couplingStrength };
        }
        sum = addComplex(sum, mulComplex(element, stateVec[j]));
      }
      projected[i] = sum;
    }

    normalizeStateVector(projected);
    return projected;
  }

  computeFidelity(original: Complex[], projected: Complex[]): number {
    if (original.length !== projected.length) return 0.0;
    let inner = complex(0, 0);
    for (let i = 0; i < original.length; i++) {
      inner = addComplex(inner, mulComplex(conjComplex(original[i]), projected[i]));
    }
    return Math.min(1.0, Math.max(0.0, absComplex(inner)));
  }

  computeCoherencePreservation(originalCoherence: number, projectedVec: Complex[]): number {
    const projectedCoherence = computeStateCoherence(projectedVec);
    if (originalCoherence < 1e-10) return 1.0;
    const preservation = projectedCoherence / originalCoherence;
    return Math.min(1.0, Math.max(0.0, preservation));
  }

  updateAdaptiveParameters(fidelity: number, coherencePres: number, targetFidelity: number): void {
    if (!this.adaptiveMode) return;
    const fidelityError = targetFidelity - fidelity;
    this.couplingStrength *= 1.0 + 0.05 * fidelityError;
    if (this.coherencePreserve && coherencePres < 0.95) {
      this.phaseFactor *= 0.95;
    }
    this.couplingStrength = Math.max(0.1, Math.min(10.0, this.couplingStrength));
    this.phaseFactor = Math.max(-Math.PI, Math.min(Math.PI, this.phaseFactor));
    this.totalUses++;
    const n = this.totalUses;
    this.avgFidelity = (this.avgFidelity * (n - 1) + fidelity) / n;
    this.avgCoherencePres = (this.avgCoherencePres * (n - 1) + coherencePres) / n;
    this.lastApplied = new Date();
  }

  getOperatorHash(): string {
    const matrixSample = JSON.stringify(this.projectionMatrix.slice(0, 10));
    const canonical = `${this.operatorID}:${this.operatorType}:${this.sourceLayer}:${this.targetLayer}:${this.sourceDim}:${this.targetDim}:${hashString(matrixSample)}`;
    return hashString(canonical).slice(0, 32);
  }
}

function generateAPIProjectionMatrix(
  opType: ProjectionOperatorType,
  sourceLayer: APILayerType,
  targetLayer: APILayerType,
  sourceDim: number,
  targetDim: number
): { matrix: Complex[][]; phase: number } {
  const matrix: Complex[][] = [];
  let phaseFactor = 0;

  switch (opType) {
    case 'ascend':
      phaseFactor = Math.PI / 4;
      for (let i = 0; i < targetDim; i++) {
        matrix[i] = [];
        for (let j = 0; j < sourceDim; j++) {
          if (i < sourceDim && i === j) {
            matrix[i][j] = complex(1.0 / Math.sqrt(targetDim), 0);
          } else if (i < targetDim / 2 && j < sourceDim / 2) {
            matrix[i][j] = complex(0.1 / Math.sqrt(targetDim), 0);
          } else {
            matrix[i][j] = complex(0, 0);
          }
        }
      }
      break;

    case 'descend':
      phaseFactor = -Math.PI / 4;
      for (let i = 0; i < targetDim; i++) {
        matrix[i] = [];
        for (let j = 0; j < sourceDim; j++) {
          if (j < sourceDim && i % 2 === j) {
            matrix[i][j] = complex(1.0 / Math.sqrt(targetDim / 2), 0);
          } else {
            matrix[i][j] = complex(0, 0);
          }
        }
      }
      break;

    case 'lateral':
      phaseFactor = 0.0;
      for (let i = 0; i < targetDim; i++) {
        matrix[i] = [];
        for (let j = 0; j < sourceDim; j++) {
          if (i === j) {
            matrix[i][j] = complex(0.9 / Math.sqrt(targetDim), 0);
          } else if (Math.abs(i - j) <= 1) {
            matrix[i][j] = complex(0.15 / Math.sqrt(targetDim), 0);
          } else {
            matrix[i][j] = complex(0, 0);
          }
        }
      }
      break;

    case 'merge':
      phaseFactor = 0.0;
      for (let i = 0; i < targetDim; i++) {
        matrix[i] = [];
        for (let j = 0; j < sourceDim; j++) {
          matrix[i][j] = complex(1.0 / Math.sqrt(sourceDim * targetDim), 0);
        }
      }
      break;

    case 'split':
      phaseFactor = 0.0;
      for (let i = 0; i < targetDim; i++) {
        matrix[i] = [];
        for (let j = 0; j < sourceDim; j++) {
          matrix[i][j] = complex(0, 0);
        }
        const srcIdx = i % sourceDim;
        matrix[i][srcIdx] = complex(1.0 / Math.sqrt(targetDim / sourceDim), 0);
      }
      break;
  }

  return { matrix, phase: phaseFactor };
}

// ─── MOTOR DE PROJEÇÃO ──────────────────────────────────
export interface ProjectionResult {
  resultID: string;
  sourceStateID: string;
  targetStateID: string;
  operatorID: string;
  operatorType: ProjectionOperatorType;
  sourceLayer: APILayerType;
  targetLayer: APILayerType;
  projectedStateVec: Complex[];
  fidelity: number;
  coherencePreserved: number;
  timestamp: Date;
  validationHash: string;
}

export interface ProjectionEngineConfig {
  enableAuditLogging: boolean;
  fidelityThreshold: number;
  coherencePreserveMode: boolean;
  adaptiveOperators: boolean;
  maxCacheSize: number;
}

export interface ProjectionMetrics {
  projectionsApplied: number;
  projectionsValidated: number;
  avgFidelity: number;
  avgCoherencePreserved: number;
  cacheHits: number;
  cacheMisses: number;
  fidelityFailures: number;
}

export class APIProjectionEngine {
  engineID: string;
  localConsciousnessHash: string;
  registeredOperators: Map<string, DimensionalProjectionOperator>;
  projectionCache: Map<string, ProjectionResult>;
  apiStates: Map<string, APIStateVector>;
  config: ProjectionEngineConfig;
  metrics: ProjectionMetrics;
  projectionCallbacks: Array<(event: ProjectionEvent) => void>;

  constructor(
    engineID: string,
    localConsciousnessHash: string,
    config: ProjectionEngineConfig
  ) {
    this.engineID = engineID;
    this.localConsciousnessHash = localConsciousnessHash;
    this.config = {
      fidelityThreshold: config.fidelityThreshold || 0.99,
      maxCacheSize: config.maxCacheSize || 100,
      enableAuditLogging: config.enableAuditLogging,
      coherencePreserveMode: config.coherencePreserveMode ?? true,
      adaptiveOperators: config.adaptiveOperators ?? true
    };
    this.registeredOperators = new Map();
    this.projectionCache = new Map();
    this.apiStates = new Map();
    this.metrics = {
      projectionsApplied: 0,
      projectionsValidated: 0,
      avgFidelity: 1.0,
      avgCoherencePreserved: 1.0,
      cacheHits: 0,
      cacheMisses: 0,
      fidelityFailures: 0
    };
    this.projectionCallbacks = [];
    this.registerDefaultOperators();
  }

  private registerDefaultOperators(): void {
    const transitions = [
      { from: 'code' as APILayerType, to: 'data' as APILayerType, fromDim: 256, toDim: 512, opType: 'ascend' as ProjectionOperatorType },
      { from: 'data' as APILayerType, to: 'infra' as APILayerType, fromDim: 512, toDim: 384, opType: 'ascend' as ProjectionOperatorType },
      { from: 'infra' as APILayerType, to: 'protocol' as APILayerType, fromDim: 384, toDim: 448, opType: 'ascend' as ProjectionOperatorType },
      { from: 'protocol' as APILayerType, to: 'meta' as APILayerType, fromDim: 448, toDim: 1024, opType: 'ascend' as ProjectionOperatorType },
      { from: 'data' as APILayerType, to: 'code' as APILayerType, fromDim: 512, toDim: 256, opType: 'descend' as ProjectionOperatorType },
      { from: 'infra' as APILayerType, to: 'data' as APILayerType, fromDim: 384, toDim: 512, opType: 'descend' as ProjectionOperatorType },
      { from: 'code' as APILayerType, to: 'code' as APILayerType, fromDim: 256, toDim: 256, opType: 'lateral' as ProjectionOperatorType },
      { from: 'data' as APILayerType, to: 'data' as APILayerType, fromDim: 512, toDim: 512, opType: 'lateral' as ProjectionOperatorType },
    ];

    for (const t of transitions) {
      const opID = `op_${t.opType}_${t.from}_${t.to}`;
      const op = new DimensionalProjectionOperator(
        opID, t.opType, t.from, t.to, t.fromDim, t.toDim, this.config.adaptiveOperators
      );
      this.registeredOperators.set(opID, op);
    }
  }

  registerAPIState(state: APIStateVector): void {
    if (state.coherenceValue < 0.70) {
      throw new Error(`API coherence ${state.coherenceValue.toFixed(3)} below minimum 0.700 for projection`);
    }
    this.apiStates.set(state.vectorID, state);
  }

  projectAPIState(
    sourceStateID: string,
    targetLayer: APILayerType,
    operatorType: ProjectionOperatorType,
    customOperatorID?: string
  ): ProjectionResult {
    const sourceState = this.apiStates.get(sourceStateID);
    if (!sourceState) {
      throw new Error(`Source state not found: ${sourceStateID}`);
    }

    // Verificar cache
    const cacheKey = `${sourceStateID}:${targetLayer}:${operatorType}`;
    const cached = this.projectionCache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp.getTime() < 3600000) {
      this.metrics.cacheHits++;
      return cached;
    }
    this.metrics.cacheMisses++;

    // Obter operador
    const operator = this.getOrCreateOperator(
      customOperatorID, operatorType,
      sourceState.layerType, targetLayer,
      sourceState.dimension, LAYER_DIMENSIONS[targetLayer]
    );

    // Aplicar projeção
    const projectedVec = operator.apply(sourceState.stateVector);

    // Calcular métricas
    const fidelity = operator.computeFidelity(sourceState.stateVector, projectedVec);
    const coherencePres = operator.computeCoherencePreservation(
      sourceState.coherenceValue, projectedVec
    );

    if (fidelity < this.config.fidelityThreshold) {
      this.metrics.fidelityFailures++;
      throw new Error(`Projection fidelity ${fidelity.toFixed(4)} below threshold ${this.config.fidelityThreshold.toFixed(4)}`);
    }

    // Criar estado alvo
    const targetState = new APIStateVector(
      sourceState.apiID,
      targetLayer,
      sourceState.layerIndex + (LAYER_INDICES[targetLayer] - LAYER_INDICES[sourceState.layerType]),
      projectedVec.length
    );
    targetState.stateVector = projectedVec;
    targetState.coherenceValue = sourceState.coherenceValue * coherencePres;
    targetState.fidelityScore = fidelity;

    // Registrar projeção
    const record: ProjectionRecord = {
      recordID: `proj_${Date.now()}`,
      timestamp: new Date(),
      sourceLayer: sourceState.layerType,
      targetLayer,
      operatorType,
      fidelity,
      coherenceDelta: coherencePres - 1.0,
      operatorHash: operator.getOperatorHash()
    };
    sourceState.addProjectionRecord(record);
    targetState.parentProjections.push(sourceState.vectorID);

    const result: ProjectionResult = {
      resultID: `result_${sourceStateID.slice(0, 8)}_${Date.now()}`,
      sourceStateID,
      targetStateID: targetState.vectorID,
      operatorID: operator.operatorID,
      operatorType,
      sourceLayer: sourceState.layerType,
      targetLayer,
      projectedStateVec: projectedVec,
      fidelity,
      coherencePreserved: coherencePres,
      timestamp: new Date(),
      validationHash: this.computeProjectionValidationHash(sourceState, targetState, operator)
    };

    // Cache e registro
    this.projectionCache.set(cacheKey, result);
    this.apiStates.set(targetState.vectorID, targetState);
    this.metrics.projectionsApplied++;
    const n = this.metrics.projectionsApplied;
    this.metrics.avgFidelity = (this.metrics.avgFidelity * (n - 1) + fidelity) / n;
    this.metrics.avgCoherencePreserved = (this.metrics.avgCoherencePreserved * (n - 1) + coherencePres) / n;

    // Notificar callbacks
    for (const cb of this.projectionCallbacks) {
      cb({
        eventType: 'projection_applied',
        apiID: sourceState.apiID,
        sourceLayer: sourceState.layerType,
        targetLayer,
        resultID: result.resultID,
        data: { fidelity, coherencePres, operatorID: operator.operatorID },
        timestamp: new Date()
      });
    }

    return result;
  }

  private getOrCreateOperator(
    customOperatorID: string | undefined,
    opType: ProjectionOperatorType,
    sourceLayer: APILayerType,
    targetLayer: APILayerType,
    sourceDim: number,
    targetDim: number
  ): DimensionalProjectionOperator {
    if (customOperatorID && this.registeredOperators.has(customOperatorID)) {
      return this.registeredOperators.get(customOperatorID)!;
    }

    for (const [_, op] of this.registeredOperators) {
      if (op.operatorType === opType &&
          op.sourceLayer === sourceLayer &&
          op.targetLayer === targetLayer &&
          op.sourceDim === sourceDim &&
          op.targetDim === targetDim) {
        return op;
      }
    }

    const opID = `auto_${opType}_${sourceLayer}_${targetLayer}_${Date.now()}`;
    return new DimensionalProjectionOperator(
      opID, opType, sourceLayer, targetLayer, sourceDim, targetDim, this.config.adaptiveOperators
    );
  }

  private computeProjectionValidationHash(
    source: APIStateVector,
    target: APIStateVector,
    operator: DimensionalProjectionOperator
  ): string {
    const canonical = `${source.getStateHash()}:${target.getStateHash()}:${operator.operatorID}:${operator.operatorType}:${operator.avgFidelity.toFixed(6)}:${operator.avgCoherencePres.toFixed(6)}:${Date.now()}`;
    return hashString(canonical).slice(0, 32);
  }

  getProjectionMetrics(): ProjectionMetrics {
    return { ...this.metrics };
  }
}

export interface ProjectionEvent {
  eventType: string;
  apiID: string;
  sourceLayer: APILayerType;
  targetLayer: APILayerType;
  resultID: string;
  data: Record<string, unknown>;
  timestamp: Date;
}
