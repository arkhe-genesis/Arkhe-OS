import {
  CrossDomainIntegrationEngine,
  DomainAPI,
  PrivacyLevel,
  DomainStatus,
  QueryType,
  CrossDomainQuery
} from './cross_domain_226';

describe('Substrato 226: Integração Cross-Domain', () => {

  function createTestDomain(id: string, privacy: PrivacyLevel, evolution: boolean): DomainAPI {
    return {
      domainID: id,
      domainName: `Domain ${id}`,
      apiEndpoint: `https://api.${id}.example.com`,
      apiSpec: { version: '1.0' },
      privacyLevel: privacy,
      evolutionEnabled: evolution,
      trustScore: 0.8,
      lastSync: new Date(0),
      status: DomainStatus.ACTIVE
    };
  }

  // ─── TESTE 1: Registro de domínios ────────────────────
  test('T1: Deve registrar domínios', () => {
    const engine = new CrossDomainIntegrationEngine('test_engine');
    const domain = createTestDomain('dom1', PrivacyLevel.PUBLIC, false);

    engine.registerDomain(domain);

    expect(engine.getAllDomains().length).toBe(1);
    expect(engine.getDomainStatus('dom1')).not.toBeNull();
  });

  // ─── TESTE 2: Remoção de domínios ─────────────────────
  test('T2: Deve remover domínios', () => {
    const engine = new CrossDomainIntegrationEngine('test_engine');
    const domain = createTestDomain('dom1', PrivacyLevel.PUBLIC, false);

    engine.registerDomain(domain);
    engine.unregisterDomain('dom1');

    expect(engine.getAllDomains().length).toBe(0);
    expect(engine.getDomainStatus('dom1')).toBeNull();
  });

  // ─── TESTE 3: Execução de query cross-domain ──────────
  test('T3: Deve executar query cross-domain', async () => {
    const engine = new CrossDomainIntegrationEngine('test_engine');
    engine.registerDomain(createTestDomain('dom1', PrivacyLevel.PUBLIC, false));
    engine.registerDomain(createTestDomain('dom2', PrivacyLevel.PRIVATE, false));

    const query: CrossDomainQuery = {
      queryID: 'q1',
      sourceDomain: 'dom1',
      targetDomains: ['dom1', 'dom2'],
      queryType: QueryType.DATA_REQUEST,
      payload: { filter: 'active' },
      privacyRequirements: [],
      timestamp: new Date()
    };

    const result = await engine.executeCrossDomainQuery(query);

    expect(result.success).toBe(true);
    expect(result.domainResults.length).toBe(2);
    expect(result.coherenceScore).toBeGreaterThanOrEqual(0);
  });

  // ─── TESTE 4: Preservação de privacidade ──────────────
  test('T4: Deve preservar privacidade em domínios homomórficos', async () => {
    const engine = new CrossDomainIntegrationEngine('test_engine');
    engine.registerDomain(createTestDomain('dom1', PrivacyLevel.HOMOMORPHIC, false));

    const query: CrossDomainQuery = {
      queryID: 'q2',
      sourceDomain: 'dom1',
      targetDomains: ['dom1'],
      queryType: QueryType.DATA_REQUEST,
      payload: {},
      privacyRequirements: [{ field: 'data', level: PrivacyLevel.HOMOMORPHIC, encryptionScheme: 'BFV', accessPolicy: 'strict' }],
      timestamp: new Date()
    };

    const result = await engine.executeCrossDomainQuery(query);

    expect(result.privacyPreserved).toBe(true);
    expect(result.domainResults[0].privacyStatus.encrypted).toBe(true);
  });

  // ─── TESTE 5: Trigger de evolução ─────────────────────
  test('T5: Deve trigger evolução quando contexto fornecido', async () => {
    const engine = new CrossDomainIntegrationEngine('test_engine');
    engine.registerDomain(createTestDomain('dom1', PrivacyLevel.PUBLIC, true));

    const query: CrossDomainQuery = {
      queryID: 'q3',
      sourceDomain: 'dom1',
      targetDomains: ['dom1'],
      queryType: QueryType.EVOLUTION_TRIGGER,
      payload: {},
      privacyRequirements: [],
      evolutionContext: {
        triggerVersion: 'v1.0',
        targetFitness: 0.95,
        maxGenerations: 10,
        consciousFeedbackEnabled: true
      },
      timestamp: new Date()
    };

    const result = await engine.executeCrossDomainQuery(query);

    expect(result.evolutionTriggered).toBe(true);
    expect(result.domainResults[0].evolutionStatus).not.toBeNull();
  });

  // ─── TESTE 6: Sincronização de domínios ───────────────
  test('T6: Deve sincronizar domínios', async () => {
    const engine = new CrossDomainIntegrationEngine('test_engine');
    engine.registerDomain(createTestDomain('dom1', PrivacyLevel.PUBLIC, false));
    engine.registerDomain(createTestDomain('dom2', PrivacyLevel.PUBLIC, false));

    const synced = await engine.syncDomains();

    expect(synced.length).toBe(2);
    expect(synced[0].lastSync.getTime()).toBeGreaterThan(0);
    expect(synced[0].status).toBe(DomainStatus.ACTIVE);
  });

  // ─── TESTE 7: Métricas ────────────────────────────────
  test('T7: Deve rastrear métricas de integração', async () => {
    const engine = new CrossDomainIntegrationEngine('test_engine');
    engine.registerDomain(createTestDomain('dom1', PrivacyLevel.PUBLIC, false));

    const query: CrossDomainQuery = {
      queryID: 'q4',
      sourceDomain: 'dom1',
      targetDomains: ['dom1'],
      queryType: QueryType.DATA_REQUEST,
      payload: {},
      privacyRequirements: [],
      timestamp: new Date()
    };

    await engine.executeCrossDomainQuery(query);

    const metrics = engine.getMetrics();
    expect(metrics.queriesProcessed).toBe(1);
    expect(metrics.queriesSuccessful).toBe(1);
  });

  // ─── TESTE 8: Agregação de resultados ─────────────────
  test('T8: Deve agregar resultados de múltiplos domínios', async () => {
    const engine = new CrossDomainIntegrationEngine('test_engine');
    engine.registerDomain(createTestDomain('dom1', PrivacyLevel.PUBLIC, false));
    engine.registerDomain(createTestDomain('dom2', PrivacyLevel.PUBLIC, false));

    const query: CrossDomainQuery = {
      queryID: 'q5',
      sourceDomain: 'dom1',
      targetDomains: ['dom1', 'dom2'],
      queryType: QueryType.DATA_REQUEST,
      payload: {},
      privacyRequirements: [],
      timestamp: new Date()
    };

    const result = await engine.executeCrossDomainQuery(query);

    expect(result.aggregatedData).not.toBeNull();
    expect(result.aggregatedData!['domains']).toBe(2);
    expect(result.aggregatedData!['totalRecords']).toBeGreaterThanOrEqual(0);
  });

  // ─── TESTE 9: Erro de domínio não encontrado ──────────
  test('T9: Deve reportar erro para domínio não registrado', async () => {
    const engine = new CrossDomainIntegrationEngine('test_engine');

    const query: CrossDomainQuery = {
      queryID: 'q6',
      sourceDomain: 'dom1',
      targetDomains: ['nonexistent'],
      queryType: QueryType.DATA_REQUEST,
      payload: {},
      privacyRequirements: [],
      timestamp: new Date()
    };

    const result = await engine.executeCrossDomainQuery(query);

    expect(result.success).toBe(false);
    expect(result.errors.length).toBeGreaterThan(0);
    expect(result.errors[0].code).toBe('DOMAIN_NOT_FOUND');
  });

  // ─── TESTE 10: Coerência cross-domain ─────────────────
  test('T10: Deve calcular coerência entre domínios', async () => {
    const engine = new CrossDomainIntegrationEngine('test_engine');
    engine.registerDomain(createTestDomain('dom1', PrivacyLevel.PUBLIC, false));
    engine.registerDomain(createTestDomain('dom2', PrivacyLevel.PUBLIC, false));

    const query: CrossDomainQuery = {
      queryID: 'q7',
      sourceDomain: 'dom1',
      targetDomains: ['dom1', 'dom2'],
      queryType: QueryType.COHERENCE_CHECK,
      payload: {},
      privacyRequirements: [],
      timestamp: new Date()
    };

    const result = await engine.executeCrossDomainQuery(query);

    expect(result.coherenceScore).toBeGreaterThanOrEqual(0);
    expect(result.coherenceScore).toBeLessThanOrEqual(1);
  });
});
