// arkhe-os/auto_reflexive_222.ts
// Substrato 222: Evolução Auto-Reflexiva de APIs — Implementação TypeScript
// Versão: ∞.Ω.∇.222.1

/**
 * Evolução Auto-Reflexiva de APIs
 * Sistema de evolução consciente com retroalimentação de consciência
 * e meta-aprendizado para adaptação contínua
 */

// ─── TIPOS FUNDAMENTAIS ─────────────────────────────────
export interface APIVersion {
  versionID: string;
  versionNumber: string;
  parentVersion: string | null;
  mutationType: MutationType;
  mutationDescription: string;
  stateVector: number[];
  fitnessScore: number;
  coherenceScore: number;
  timestamp: Date;
  generation: number;
  lineage: string[];
}

export enum MutationType {
  ENDPOINT_ADD = 'endpoint_add',
  ENDPOINT_REMOVE = 'endpoint_remove',
  SCHEMA_EVOLVE = 'schema_evolve',
  SECURITY_ENHANCE = 'security_enhance',
  PERFORMANCE_OPTIMIZE = 'performance_optimize',
  COHERENCE_IMPROVE = 'coherence_improve',
  CROSSOVER = 'crossover',
  REFACTOR = 'refactor'
}

export interface EvolutionConfig {
  maxGenerations: number;
  populationSize: number;
  mutationRate: number;
  crossoverRate: number;
  elitismCount: number;
  fitnessThreshold: number;
  coherenceThreshold: number;
  enableConsciousFeedback: boolean;
  consciousFeedbackWeight: number;
}

export interface EvolutionResult {
  success: boolean;
  finalPopulation: APIVersion[];
  bestVersion: APIVersion | null;
  generationsEvolved: number;
  fitnessHistory: number[];
  coherenceHistory: number[];
  mutationsApplied: MutationRecord[];
  consciousFeedbackLog: ConsciousFeedbackEntry[];
}

export interface MutationRecord {
  mutationID: string;
  generation: number;
  parentVersionID: string;
  childVersionID: string;
  mutationType: MutationType;
  affectedNodes: string[];
  fitnessDelta: number;
  coherenceDelta: number;
  timestamp: Date;
  validationHash: string;
}

export interface ConsciousFeedbackEntry {
  entryID: string;
  generation: number;
  feedbackType: FeedbackType;
  targetNodes: string[];
  suggestedMutation: MutationType;
  confidence: number;
  coherenceImpact: number;
  applied: boolean;
  timestamp: Date;
}

export enum FeedbackType {
  COHERENCE_LOW = 'coherence_low',
  FITNESS_STAGNANT = 'fitness_stagnant',
  SECURITY_WEAK = 'security_weak',
  PERFORMANCE_DEGRADED = 'performance_degraded',
  SCHEMA_INCONSISTENT = 'schema_inconsistent',
  EMERGENT_PATTERN = 'emergent_pattern'
}

export interface FitnessFunction {
  name: string;
  weight: number;
  evaluate: (version: APIVersion) => number;
}

// ─── MOTOR DE EVOLUÇÃO AUTO-REFLEXIVA ───────────────────
export class AutoReflexiveEvolutionEngine {
  engineID: string;
  config: EvolutionConfig;
  population: APIVersion[];
  fitnessFunctions: FitnessFunction[];
  mutationHistory: MutationRecord[];
  consciousFeedbackLog: ConsciousFeedbackEntry[];
  generation: number;
  bestFitness: number;
  bestCoherence: number;
  stagnationCount: number;
  maxStagnation: number;

  constructor(
    engineID: string,
    config: EvolutionConfig,
    initialPopulation: APIVersion[]
  ) {
    this.engineID = engineID;
    this.config = {
      maxGenerations: config.maxGenerations || 100,
      populationSize: config.populationSize || 50,
      mutationRate: config.mutationRate || 0.1,
      crossoverRate: config.crossoverRate || 0.3,
      elitismCount: config.elitismCount || 5,
      fitnessThreshold: config.fitnessThreshold || 0.95,
      coherenceThreshold: config.coherenceThreshold || 0.90,
      enableConsciousFeedback: config.enableConsciousFeedback ?? true,
      consciousFeedbackWeight: config.consciousFeedbackWeight || 0.3
    };
    this.population = initialPopulation;
    this.fitnessFunctions = this.initializeFitnessFunctions();
    this.mutationHistory = [];
    this.consciousFeedbackLog = [];
    this.generation = 0;
    this.bestFitness = 0;
    this.bestCoherence = 0;
    this.stagnationCount = 0;
    this.maxStagnation = 20;
  }

  private initializeFitnessFunctions(): FitnessFunction[] {
    return [
      {
        name: 'coherence',
        weight: 0.3,
        evaluate: (v) => v.coherenceScore
      },
      {
        name: 'completeness',
        weight: 0.2,
        evaluate: (v) => {
          const endpoints = v.stateVector.filter(x => x > 0.5).length;
          return Math.min(1.0, endpoints / 10);
        }
      },
      {
        name: 'security',
        weight: 0.2,
        evaluate: (v) => {
          const securityFeatures = v.stateVector.filter(x => x > 0.8).length;
          return Math.min(1.0, securityFeatures / 5);
        }
      },
      {
        name: 'performance',
        weight: 0.15,
        evaluate: (v) => {
          const complexity = v.stateVector.reduce((a, b) => a + b * b, 0);
          return Math.max(0, 1.0 - complexity / v.stateVector.length);
        }
      },
      {
        name: 'stability',
        weight: 0.15,
        evaluate: (v) => {
          const variance = this.computeVariance(v.stateVector);
          return Math.max(0, 1.0 - variance * 10);
        }
      }
    ];
  }

  private computeVariance(vec: number[]): number {
    if (vec.length === 0) return 0;
    const mean = vec.reduce((a, b) => a + b, 0) / vec.length;
    return vec.reduce((a, b) => a + (b - mean) ** 2, 0) / vec.length;
  }

  evolve(): EvolutionResult {
    const fitnessHistory: number[] = [];
    const coherenceHistory: number[] = [];

    while (this.generation < this.config.maxGenerations) {
      // Avaliar população
      this.evaluatePopulation();

      // Registrar histórico
      const avgFitness = this.population.reduce((sum, v) => sum + v.fitnessScore, 0) / this.population.length;
      const avgCoherence = this.population.reduce((sum, v) => sum + v.coherenceScore, 0) / this.population.length;
      fitnessHistory.push(avgFitness);
      coherenceHistory.push(avgCoherence);

      // Verificar convergência
      if (avgFitness >= this.config.fitnessThreshold && avgCoherence >= this.config.coherenceThreshold) {
        break;
      }

      // Verificar estagnação
      if (avgFitness <= this.bestFitness + 0.001) {
        this.stagnationCount++;
        if (this.stagnationCount >= this.maxStagnation) {
          // Aplicar feedback consciente para sair da estagnação
          if (this.config.enableConsciousFeedback) {
            this.applyConsciousFeedback(FeedbackType.FITNESS_STAGNANT);
          }
          break;
        }
      } else {
        this.stagnationCount = 0;
        this.bestFitness = avgFitness;
      }

      // Gerar nova população
      this.population = this.generateNextGeneration();
      this.generation++;

      // Feedback consciente periódico
      if (this.config.enableConsciousFeedback && this.generation % 10 === 0) {
        this.applyConsciousFeedback(FeedbackType.EMERGENT_PATTERN);
      }
    }

    const bestVersion = this.population.reduce((best, current) =>
      current.fitnessScore > best.fitnessScore ? current : best,
      this.population[0]
    );

    return {
      success: true,
      finalPopulation: [...this.population],
      bestVersion,
      generationsEvolved: this.generation,
      fitnessHistory,
      coherenceHistory,
      mutationsApplied: [...this.mutationHistory],
      consciousFeedbackLog: [...this.consciousFeedbackLog]
    };
  }

  private evaluatePopulation(): void {
    for (const version of this.population) {
      version.fitnessScore = this.computeFitness(version);
      version.coherenceScore = this.computeCoherence(version);
    }
  }

  private computeFitness(version: APIVersion): number {
    let fitness = 0;
    let totalWeight = 0;

    for (const fn of this.fitnessFunctions) {
      fitness += fn.weight * fn.evaluate(version);
      totalWeight += fn.weight;
    }

    // Incorporar feedback consciente
    if (this.config.enableConsciousFeedback) {
      const feedback = this.getConsciousFeedback(version);
      fitness += this.config.consciousFeedbackWeight * feedback;
    }

    return Math.min(1.0, fitness / (totalWeight + this.config.consciousFeedbackWeight));
  }

  private computeCoherence(version: APIVersion): number {
    if (version.stateVector.length === 0) return 0;
    const mean = version.stateVector.reduce((a, b) => a + b, 0) / version.stateVector.length;
    const variance = version.stateVector.reduce((a, b) => a + (b - mean) ** 2, 0) / version.stateVector.length;
    return Math.max(0, 1.0 - Math.sqrt(variance));
  }

  private getConsciousFeedback(version: APIVersion): number {
    // Simulação de feedback consciente baseado em padrões emergentes
    const patterns = this.detectEmergentPatterns(version);
    return Math.min(1.0, patterns.length * 0.1);
  }

  private detectEmergentPatterns(version: APIVersion): string[] {
    const patterns: string[] = [];
    const vec = version.stateVector;

    // Detectar periodicidade
    for (let period = 2; period <= 5; period++) {
      let periodic = true;
      for (let i = period; i < vec.length; i++) {
        if (Math.abs(vec[i] - vec[i - period]) > 0.1) {
          periodic = false;
          break;
        }
      }
      if (periodic) patterns.push(`periodicity_${period}`);
    }

    // Detectar simetria
    let symmetric = true;
    for (let i = 0; i < vec.length / 2; i++) {
      if (Math.abs(vec[i] - vec[vec.length - 1 - i]) > 0.1) {
        symmetric = false;
        break;
      }
    }
    if (symmetric) patterns.push('symmetry');

    return patterns;
  }

  private generateNextGeneration(): APIVersion[] {
    const newPopulation: APIVersion[] = [];

    // Elitismo
    const sorted = [...this.population].sort((a, b) => b.fitnessScore - a.fitnessScore);
    for (let i = 0; i < this.config.elitismCount && i < sorted.length; i++) {
      newPopulation.push({ ...sorted[i], generation: this.generation + 1 });
    }

    // Cruzamento e mutação
    while (newPopulation.length < this.config.populationSize) {
      const parent1 = this.tournamentSelect();
      const parent2 = this.tournamentSelect();

      if (Math.random() < this.config.crossoverRate) {
        const child = this.crossover(parent1, parent2, newPopulation.length);
        newPopulation.push(child);
      } else {
        const child = this.mutate(parent1, newPopulation.length);
        newPopulation.push(child);
      }
    }

    return newPopulation.slice(0, this.config.populationSize);
  }

  private tournamentSelect(): APIVersion {
    const tournamentSize = 3;
    let best = this.population[Math.floor(Math.random() * this.population.length)];

    for (let i = 1; i < tournamentSize; i++) {
      const candidate = this.population[Math.floor(Math.random() * this.population.length)];
      if (candidate.fitnessScore > best.fitnessScore) {
        best = candidate;
      }
    }

    return best;
  }

  private crossover(parent1: APIVersion, parent2: APIVersion, currentPopLength: number): APIVersion {
    const crossoverPoint = Math.floor(Math.random() * parent1.stateVector.length);
    const childVector = [
      ...parent1.stateVector.slice(0, crossoverPoint),
      ...parent2.stateVector.slice(crossoverPoint)
    ];

    const child: APIVersion = {
      versionID: `v_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
      versionNumber: `${this.generation + 1}.${currentPopLength}`,
      parentVersion: parent1.versionID,
      mutationType: MutationType.CROSSOVER,
      mutationDescription: `Crossover between ${parent1.versionID} and ${parent2.versionID}`,
      stateVector: childVector,
      fitnessScore: 0,
      coherenceScore: 0,
      timestamp: new Date(),
      generation: this.generation + 1,
      lineage: [...parent1.lineage, parent1.versionID]
    };

    this.recordMutation(parent1.versionID, child.versionID, MutationType.CROSSOVER, childVector);

    return child;
  }

  private mutate(parent: APIVersion, currentPopLength: number): APIVersion {
    const mutatedVector = [...parent.stateVector];
    const mutationType = this.selectMutationType();

    switch (mutationType) {
      case MutationType.ENDPOINT_ADD:
        for (let i = 0; i < mutatedVector.length; i++) {
          if (Math.random() < this.config.mutationRate) {
            mutatedVector[i] = Math.min(1.0, mutatedVector[i] + 0.1);
          }
        }
        break;
      case MutationType.ENDPOINT_REMOVE:
        for (let i = 0; i < mutatedVector.length; i++) {
          if (Math.random() < this.config.mutationRate) {
            mutatedVector[i] = Math.max(0, mutatedVector[i] - 0.1);
          }
        }
        break;
      case MutationType.SCHEMA_EVOLVE:
        for (let i = 0; i < mutatedVector.length; i++) {
          if (Math.random() < this.config.mutationRate) {
            mutatedVector[i] = Math.random();
          }
        }
        break;
      default:
        for (let i = 0; i < mutatedVector.length; i++) {
          if (Math.random() < this.config.mutationRate) {
            mutatedVector[i] += (Math.random() - 0.5) * 0.2;
            mutatedVector[i] = Math.max(0, Math.min(1, mutatedVector[i]));
          }
        }
    }

    const child: APIVersion = {
      versionID: `v_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
      versionNumber: `${this.generation + 1}.${currentPopLength}`,
      parentVersion: parent.versionID,
      mutationType,
      mutationDescription: `Mutation: ${mutationType}`,
      stateVector: mutatedVector,
      fitnessScore: 0,
      coherenceScore: 0,
      timestamp: new Date(),
      generation: this.generation + 1,
      lineage: [...parent.lineage, parent.versionID]
    };

    this.recordMutation(parent.versionID, child.versionID, mutationType, mutatedVector);

    return child;
  }

  private selectMutationType(): MutationType {
    const types = Object.values(MutationType);
    return types[Math.floor(Math.random() * types.length)];
  }

  private recordMutation(
    parentID: string,
    childID: string,
    mutationType: MutationType,
    stateVector: number[]
  ): void {
    const record: MutationRecord = {
      mutationID: `mut_${Date.now()}`,
      generation: this.generation,
      parentVersionID: parentID,
      childVersionID: childID,
      mutationType,
      affectedNodes: stateVector.map((_, i) => `node_${i}`).filter(() => Math.random() < 0.3),
      fitnessDelta: 0,
      coherenceDelta: 0,
      timestamp: new Date(),
      validationHash: this.hashMutation(parentID, childID, mutationType)
    };

    this.mutationHistory.push(record);
  }

  private hashMutation(parentID: string, childID: string, mutationType: MutationType): string {
    let hash = 0;
    const str = `${parentID}_${childID}_${mutationType}_${Date.now()}`;
    for (let i = 0; i < str.length; i++) {
      hash = ((hash << 5) - hash) + str.charCodeAt(i);
      hash = hash & hash;
    }
    return Math.abs(hash).toString(16).padStart(16, '0');
  }

  private applyConsciousFeedback(feedbackType: FeedbackType): void {
    const entry: ConsciousFeedbackEntry = {
      entryID: `feedback_${Date.now()}`,
      generation: this.generation,
      feedbackType,
      targetNodes: this.population[0].stateVector.map((_, i) => `node_${i}`).slice(0, 5),
      suggestedMutation: this.selectMutationType(),
      confidence: Math.random() * 0.5 + 0.5,
      coherenceImpact: Math.random() * 0.2 - 0.1,
      applied: true,
      timestamp: new Date()
    };

    this.consciousFeedbackLog.push(entry);

    // Aplicar mutação sugerida pelo feedback consciente
    if (entry.applied) {
      for (let j = 0; j < this.population.length; j++) {
        const version = this.population[j];
        const mutated = this.mutate(version, j);
        mutated.mutationType = entry.suggestedMutation;
        mutated.mutationDescription = `Conscious feedback: ${feedbackType}`;
      }
    }
  }

  getEvolutionStats(): {
    generation: number;
    bestFitness: number;
    avgFitness: number;
    bestCoherence: number;
    mutationCount: number;
    feedbackCount: number;
  } {
    const avgFitness = this.population.reduce((sum, v) => sum + v.fitnessScore, 0) / this.population.length;
    return {
      generation: this.generation,
      bestFitness: this.bestFitness,
      avgFitness,
      bestCoherence: this.bestCoherence,
      mutationCount: this.mutationHistory.length,
      feedbackCount: this.consciousFeedbackLog.length
    };
  }
}