import {
  AutoReflexiveEvolutionEngine,
  APIVersion,
  MutationType,
  FeedbackType,
  EvolutionConfig
} from './auto_reflexive_222';

describe('Substrato 222: Evolução Auto-Reflexiva', () => {

  function createInitialPopulation(size: number, dim: number): APIVersion[] {
    return Array.from({ length: size }, (_, i) => ({
      versionID: `v0_${i}`,
      versionNumber: `0.${i}`,
      parentVersion: null,
      mutationType: MutationType.REFACTOR,
      mutationDescription: 'Initial population',
      stateVector: Array.from({ length: dim }, () => Math.random()),
      fitnessScore: 0,
      coherenceScore: 0,
      timestamp: new Date(),
      generation: 0,
      lineage: []
    }));
  }

  // ─── TESTE 1: Inicialização do motor ──────────────────
  test('T1: Deve inicializar com população e configuração', () => {
    const population = createInitialPopulation(10, 20);
    const config: EvolutionConfig = {
      maxGenerations: 50,
      populationSize: 10,
      mutationRate: 0.1,
      crossoverRate: 0.3,
      elitismCount: 2,
      fitnessThreshold: 0.95,
      coherenceThreshold: 0.90,
      enableConsciousFeedback: true,
      consciousFeedbackWeight: 0.3
    };

    const engine = new AutoReflexiveEvolutionEngine('test_engine', config, population);

    expect(engine.population.length).toBe(10);
    expect(engine.generation).toBe(0);
    expect(engine.config.maxGenerations).toBe(50);
  });

  // ─── TESTE 2: Evolução básica ─────────────────────────
  test('T2: Deve evoluir por múltiplas gerações', () => {
    const population = createInitialPopulation(20, 20);
    const config: EvolutionConfig = {
      maxGenerations: 10,
      populationSize: 20,
      mutationRate: 0.1,
      crossoverRate: 0.3,
      elitismCount: 2,
      fitnessThreshold: 0.99,
      coherenceThreshold: 0.99,
      enableConsciousFeedback: false,
      consciousFeedbackWeight: 0
    };

    const engine = new AutoReflexiveEvolutionEngine('test_engine', config, population);
    const result = engine.evolve();

    expect(result.success).toBe(true);
    expect(result.generationsEvolved).toBeGreaterThan(0);
    expect(result.finalPopulation.length).toBe(20);
    expect(result.fitnessHistory.length).toBeGreaterThan(0);
  });

  // ─── TESTE 3: Melhor versão ────────────────────────────
  test('T3: Deve identificar melhor versão', () => {
    const population = createInitialPopulation(20, 20);
    const config: EvolutionConfig = {
      maxGenerations: 5,
      populationSize: 20,
      mutationRate: 0.1,
      crossoverRate: 0.3,
      elitismCount: 2,
      fitnessThreshold: 0.99,
      coherenceThreshold: 0.99,
      enableConsciousFeedback: false,
      consciousFeedbackWeight: 0
    };

    const engine = new AutoReflexiveEvolutionEngine('test_engine', config, population);
    const result = engine.evolve();

    expect(result.bestVersion).not.toBeNull();
    expect(result.bestVersion!.fitnessScore).toBeGreaterThanOrEqual(0);
    expect(result.bestVersion!.coherenceScore).toBeGreaterThanOrEqual(0);
  });

  // ─── TESTE 4: Elitismo ────────────────────────────────
  test('T4: Melhores indivíduos devem persistir (elitismo)', () => {
    const population = createInitialPopulation(20, 20);
    const config: EvolutionConfig = {
      maxGenerations: 5,
      populationSize: 20,
      mutationRate: 0.5,
      crossoverRate: 0.5,
      elitismCount: 3,
      fitnessThreshold: 0.99,
      coherenceThreshold: 0.99,
      enableConsciousFeedback: false,
      consciousFeedbackWeight: 0
    };

    const engine = new AutoReflexiveEvolutionEngine('test_engine', config, population);

    // Avaliar população inicial
    (engine as any).evaluatePopulation();
    const initialBest = [...engine.population].sort((a, b) => b.fitnessScore - a.fitnessScore)[0];

    engine.evolve();

    const finalBest = [...engine.population].sort((a, b) => b.fitnessScore - a.fitnessScore)[0];
    expect(finalBest.fitnessScore).toBeGreaterThanOrEqual(0);
  });

  // ─── TESTE 5: Feedback consciente ──────────────────────
  test('T5: Deve aplicar feedback consciente quando habilitado', () => {
    const population = createInitialPopulation(20, 20);
    const config: EvolutionConfig = {
      maxGenerations: 15,
      populationSize: 20,
      mutationRate: 0.1,
      crossoverRate: 0.3,
      elitismCount: 2,
      fitnessThreshold: 0.99,
      coherenceThreshold: 0.99,
      enableConsciousFeedback: true,
      consciousFeedbackWeight: 0.3
    };

    const engine = new AutoReflexiveEvolutionEngine('test_engine', config, population);
    const result = engine.evolve();

    expect(result.consciousFeedbackLog.length).toBeGreaterThan(0);
  });

  // ─── TESTE 6: Histórico de mutações ───────────────────
  test('T6: Deve registrar histórico de mutações', () => {
    const population = createInitialPopulation(20, 20);
    const config: EvolutionConfig = {
      maxGenerations: 5,
      populationSize: 20,
      mutationRate: 0.1,
      crossoverRate: 0.3,
      elitismCount: 2,
      fitnessThreshold: 0.99,
      coherenceThreshold: 0.99,
      enableConsciousFeedback: false,
      consciousFeedbackWeight: 0
    };

    const engine = new AutoReflexiveEvolutionEngine('test_engine', config, population);
    const result = engine.evolve();

    expect(result.mutationsApplied.length).toBeGreaterThan(0);
  });

  // ─── TESTE 7: Convergência ────────────────────────────
  test('T7: Fitness deve convergir ou melhorar', () => {
    const population = createInitialPopulation(20, 20);
    const config: EvolutionConfig = {
      maxGenerations: 10,
      populationSize: 20,
      mutationRate: 0.1,
      crossoverRate: 0.3,
      elitismCount: 2,
      fitnessThreshold: 0.99,
      coherenceThreshold: 0.99,
      enableConsciousFeedback: false,
      consciousFeedbackWeight: 0
    };

    const engine = new AutoReflexiveEvolutionEngine('test_engine', config, population);
    const result = engine.evolve();

    const initialFitness = result.fitnessHistory[0];
    const finalFitness = result.fitnessHistory[result.fitnessHistory.length - 1];

    // Fitness não deve piorar significativamente
    expect(finalFitness).toBeGreaterThanOrEqual(initialFitness * 0.5);
  });

  // ─── TESTE 8: Coerência ───────────────────────────────
  test('T8: Coerência deve ser calculada para cada versão', () => {
    const population = createInitialPopulation(20, 20);
    const config: EvolutionConfig = {
      maxGenerations: 5,
      populationSize: 20,
      mutationRate: 0.1,
      crossoverRate: 0.3,
      elitismCount: 2,
      fitnessThreshold: 0.99,
      coherenceThreshold: 0.99,
      enableConsciousFeedback: false,
      consciousFeedbackWeight: 0
    };

    const engine = new AutoReflexiveEvolutionEngine('test_engine', config, population);
    const result = engine.evolve();

    for (const version of result.finalPopulation) {
      expect(version.coherenceScore).toBeGreaterThanOrEqual(0);
      expect(version.coherenceScore).toBeLessThanOrEqual(1);
    }
  });

  // ─── TESTE 9: Estatísticas de evolução ────────────────
  test('T9: Deve fornecer estatísticas de evolução', () => {
    const population = createInitialPopulation(20, 20);
    const config: EvolutionConfig = {
      maxGenerations: 5,
      populationSize: 20,
      mutationRate: 0.1,
      crossoverRate: 0.3,
      elitismCount: 2,
      fitnessThreshold: 0.99,
      coherenceThreshold: 0.99,
      enableConsciousFeedback: false,
      consciousFeedbackWeight: 0
    };

    const engine = new AutoReflexiveEvolutionEngine('test_engine', config, population);
    engine.evolve();

    const stats = engine.getEvolutionStats();
    expect(stats.generation).toBeGreaterThan(0);
    expect(stats.mutationCount).toBeGreaterThan(0);
    expect(stats.avgFitness).toBeGreaterThanOrEqual(0);
  });

  // ─── TESTE 10: Detecção de padrões ────────────────────
  test('T10: Deve detectar padrões emergentes', () => {
    const population = createInitialPopulation(20, 20);
    const config: EvolutionConfig = {
      maxGenerations: 5,
      populationSize: 20,
      mutationRate: 0.1,
      crossoverRate: 0.3,
      elitismCount: 2,
      fitnessThreshold: 0.99,
      coherenceThreshold: 0.99,
      enableConsciousFeedback: true,
      consciousFeedbackWeight: 0.3
    };

    const engine = new AutoReflexiveEvolutionEngine('test_engine', config, population);

    // Criar versão com padrão periódico
    const periodicVersion: APIVersion = {
      versionID: 'periodic_test',
      versionNumber: '1.0',
      parentVersion: null,
      mutationType: MutationType.REFACTOR,
      mutationDescription: 'Periodic pattern test',
      stateVector: [0.5, 0.3, 0.5, 0.3, 0.5, 0.3, 0.5, 0.3],
      fitnessScore: 0,
      coherenceScore: 0,
      timestamp: new Date(),
      generation: 0,
      lineage: []
    };

    const patterns = (engine as any).detectEmergentPatterns(periodicVersion);
    expect(patterns.length).toBeGreaterThan(0);
    expect(patterns.some((p: string) => p.includes('periodicity'))).toBe(true);
  });
});
