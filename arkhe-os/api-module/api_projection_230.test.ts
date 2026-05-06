import {
  APIStateVector,
  DimensionalProjectionOperator,
  APIProjectionEngine,
  Complex,
  complex,
  absComplex,
  APILayerType,
  ProjectionOperatorType,
  LAYER_DIMENSIONS,
  computeStateCoherence,
  normalizeStateVector
} from './api_projection_230';

describe('Substrato 230: API 5D Projection', () => {

  // ─── TESTE 1: Normalização de Vetor de Estado ─────────
  test('T1: Vetor de estado deve ter norma unitária após normalização', () => {
    const vec: Complex[] = [
      complex(1, 0), complex(2, 1), complex(0, 3), complex(-1, 2)
    ];
    normalizeStateVector(vec);

    let normSq = 0;
    for (const c of vec) {
      normSq += c.re * c.re + c.im * c.im;
    }

    expect(Math.abs(normSq - 1.0)).toBeLessThan(1e-10);
  });

  // ─── TESTE 2: Coerência de Estado ─────────────────────
  test('T2: Coerência deve estar em [0, 1]', () => {
    const vec: Complex[] = [];
    for (let i = 0; i < 256; i++) {
      vec.push(complex(Math.random(), Math.random()));
    }
    normalizeStateVector(vec);

    const coherence = computeStateCoherence(vec);
    expect(coherence).toBeGreaterThanOrEqual(0);
    expect(coherence).toBeLessThanOrEqual(1);
  });

  // ─── TESTE 3: Criação de APIStateVector ───────────────
  test('T3: APIStateVector deve inicializar com coerência calculada', () => {
    const state = new APIStateVector(
      'test_api_v1',
      'code',
      0,
      256
    );

    expect(state.dimension).toBe(256);
    expect(state.coherenceValue).toBeGreaterThanOrEqual(0);
    expect(state.coherenceValue).toBeLessThanOrEqual(1);
    expect(state.fidelityScore).toBe(1.0);
  });

  // ─── TESTE 4: Operador Ascend (code → data) ───────────
  test('T4: Projeção ascend deve preservar norma', () => {
    const op = new DimensionalProjectionOperator(
      'op_ascend_test',
      'ascend',
      'code',
      'data',
      256,
      512,
      false
    );

    // Estado aleatório normalizado
    const psi: Complex[] = [];
    for (let i = 0; i < 256; i++) {
      psi.push(complex(Math.random(), Math.random()));
    }
    normalizeStateVector(psi);

    const projected = op.apply(psi);

    // Verificar dimensão
    expect(projected.length).toBe(512);

    // Verificar normalização
    let normSq = 0;
    for (const c of projected) {
      normSq += c.re * c.re + c.im * c.im;
    }
    expect(Math.abs(normSq - 1.0)).toBeLessThan(1e-6);
  });

  // ─── TESTE 5: Fidelidade de Projeção ──────────────────
  test('T5: Fidelidade deve ser ≥ 0.99 para projeção unitária', () => {
    const op = new DimensionalProjectionOperator(
      'op_lateral_test',
      'lateral',
      'code',
      'code',
      256,
      256,
      false
    );

    const psi: Complex[] = [];
    for (let i = 0; i < 256; i++) {
      psi.push(complex(Math.random(), Math.random()));
    }
    normalizeStateVector(psi);

    const projected = op.apply(psi);
    const fidelity = op.computeFidelity(psi, projected);

    expect(fidelity).toBeGreaterThanOrEqual(0.99);
  });

  // ─── TESTE 6: Motor de Projeção ───────────────────────
  test('T6: APIProjectionEngine deve registrar e projetar estado', () => {
    const engine = new APIProjectionEngine(
      'test_engine',
      'consciousness_test',
      {
        enableAuditLogging: false,
        fidelityThreshold: 0.99,
        coherencePreserveMode: true,
        adaptiveOperators: false,
        maxCacheSize: 10
      }
    );

    const state = new APIStateVector('api_test', 'code', 0, 256);
    engine.registerAPIState(state);

    const result = engine.projectAPIState(
      state.vectorID,
      'data',
      'ascend'
    );

    expect(result.fidelity).toBeGreaterThanOrEqual(0.99);
    expect(result.coherencePreserved).toBeGreaterThan(0);
    expect(result.projectedStateVec.length).toBe(512);
  });

  // ─── TESTE 7: Cache de Projeções ──────────────────────
  test('T7: Cache deve retornar resultado idêntico', () => {
    const engine = new APIProjectionEngine(
      'cache_test',
      'consciousness_cache',
      {
        enableAuditLogging: false,
        fidelityThreshold: 0.99,
        coherencePreserveMode: true,
        adaptiveOperators: false,
        maxCacheSize: 10
      }
    );

    const state = new APIStateVector('api_cache', 'code', 0, 256);
    engine.registerAPIState(state);

    const r1 = engine.projectAPIState(state.vectorID, 'data', 'ascend');
    const r2 = engine.projectAPIState(state.vectorID, 'data', 'ascend');

    expect(r1.resultID).toBe(r2.resultID);
    expect(engine.getProjectionMetrics().cacheHits).toBeGreaterThan(0);
  });

  // ─── TESTE 8: Dimensões de Camadas ────────────────────
  test('T8: Dimensões das camadas devem corresponder à especificação', () => {
    expect(LAYER_DIMENSIONS.code).toBe(256);
    expect(LAYER_DIMENSIONS.data).toBe(512);
    expect(LAYER_DIMENSIONS.infra).toBe(384);
    expect(LAYER_DIMENSIONS.protocol).toBe(448);
    expect(LAYER_DIMENSIONS.meta).toBe(1024);
  });

  // ─── TESTE 9: Operador Descend ────────────────────────
  test('T9: Projeção descend deve reduzir dimensão', () => {
    const op = new DimensionalProjectionOperator(
      'op_descend_test',
      'descend',
      'data',
      'code',
      512,
      256,
      false
    );

    const psi: Complex[] = [];
    for (let i = 0; i < 512; i++) {
      psi.push(complex(Math.random(), Math.random()));
    }
    normalizeStateVector(psi);

    const projected = op.apply(psi);
    expect(projected.length).toBe(256);

    // Norma deve ser preservada
    let normSq = 0;
    for (const c of projected) {
      normSq += c.re * c.re + c.im * c.im;
    }
    expect(Math.abs(normSq - 1.0)).toBeLessThan(1e-6);
  });

  // ─── TESTE 10: Métricas do Motor ─────────────────────
  test('T10: Métricas devem refletir operações realizadas', () => {
    const engine = new APIProjectionEngine(
      'metrics_test',
      'consciousness_metrics',
      {
        enableAuditLogging: false,
        fidelityThreshold: 0.99,
        coherencePreserveMode: true,
        adaptiveOperators: false,
        maxCacheSize: 10
      }
    );

    const state = new APIStateVector('api_metrics', 'code', 0, 256);
    engine.registerAPIState(state);

    engine.projectAPIState(state.vectorID, 'data', 'ascend');
    engine.projectAPIState(state.vectorID, 'infra', 'ascend');

    const metrics = engine.getProjectionMetrics();
    expect(metrics.projectionsApplied).toBe(2);
    expect(metrics.avgFidelity).toBeGreaterThanOrEqual(0.99);
  });
});
