// ============================================================================
// ARKHE Ω-TEMP — ConsistencyOracle for WebRTC Mesh
// ============================================================================
// Álgebra de Heyting aplicada a consistência de mensagens temporais.
// Otimizado para avaliação distribuída em mesh P2P.
// ============================================================================

export type Score = number; // [0, 1]

export const SCORE_ONE: Score = 1.0;
export const SCORE_ZERO: Score = 0.0;
export const SCORE_HALF: Score = 0.5;

export enum CheckName {
  Harmless = 'harmless',
  ParadoxFree = 'paradox_free',
  EntropySafe = 'entropy_safe',
  Coherent = 'coherent',
  ZKValid = 'zk_valid',
  QuantumTime = 'quantum_time',
  SolarCoherence = 'solar_coherence',
  GalacticAuth = 'galactic_auth',
}

export interface Thresholds {
  harmless: Score;
  paradoxFree: Score;
  entropySafe: Score;
  coherent: Score;
  zkValid: Score;
  quantumTime: Score;
  solarCoherence: Score;
  galacticAuth: Score;
}

export interface CheckWeights {
  [key: string]: number;
}

export interface CheckResult {
  check: CheckName;
  score: Score;
  violations: string[];
}

export interface ConsistencyReport {
  score: Score;
  adjustedWeight: number;
  pruned: boolean;
  paradoxDetected: boolean;
  checks: Map<CheckName, CheckResult>;
}

export interface ConsensusVote {
  blockIndex: number;
  blockHash: string;
  approve: boolean;
  voter: string;
  signature: Uint8Array;
}

export class TemporalConsistencyOracle {
  private static instance: TemporalConsistencyOracle;

  private thresholds: Thresholds = {
    harmless: 0.90,
    paradoxFree: 0.95,
    entropySafe: 0.70,
    coherent: 0.85,
    zkValid: 0.80,
    quantumTime: 0.95,
    solarCoherence: 0.60,
    galacticAuth: 0.50,
  };

  private weights: CheckWeights = {
    [CheckName.Harmless]: 2.0,
    [CheckName.ParadoxFree]: 3.0,
    [CheckName.EntropySafe]: 1.0,
    [CheckName.Coherent]: 1.5,
    [CheckName.ZKValid]: 1.0,
    [CheckName.QuantumTime]: 1.2,
    [CheckName.SolarCoherence]: 0.5,
    [CheckName.GalacticAuth]: 0.5,
  };

  private strictMode: boolean = false;
  private evaluations: number = 0;
  private pruned: number = 0;
  private accepted: number = 0;

  private messageCache: Map<string, ConsistencyReport> = new Map();
  private cacheMaxSize: number = 10000;

  // Singleton
  static getInstance(): TemporalConsistencyOracle {
    if (!TemporalConsistencyOracle.instance) {
      TemporalConsistencyOracle.instance = new TemporalConsistencyOracle();
    }
    return TemporalConsistencyOracle.instance;
  }

  // Avaliar consistência de uma mensagem
  evaluate(msg: any, edgeWeight: number = 1.0): ConsistencyReport {
    // Verificar cache
    const cacheKey = this.computeCacheKey(msg);
    const cached = this.messageCache.get(cacheKey);
    if (cached) return cached;

    this.evaluations++;

    const report: ConsistencyReport = {
      score: SCORE_ONE,
      adjustedWeight: 1.0,
      pruned: false,
      paradoxDetected: false,
      checks: new Map(),
    };

    let minScore = SCORE_ONE; // Meet accumulator
    let weightedSum = 0;
    let totalWeight = 0;

    const checks = Object.values(CheckName);

    for (const checkName of checks) {
      const threshold = this.getThreshold(checkName);
      const weight = this.getWeight(checkName);

      const result = this.evaluateCheck(checkName, msg, report);
      report.checks.set(checkName, result);

      // Meet: bottleneck
      if (result.score < minScore) {
        minScore = result.score;
      }

      // Weighted sum for average
      weightedSum += result.score * weight;
      totalWeight += weight;

      // Threshold check
      if (result.score < threshold) {
        report.pruned = true;
        if (this.isParadoxCheck(checkName, result)) {
          report.paradoxDetected = true;
        }
      }
    }

    // Composite score: Flex mode
    // composite = α × weighted_avg + (1-α) × bottleneck
    // α = 0.7 for flex, 1.0 for strict (= pure bottleneck)

    if (totalWeight > 0) {
      const avgScore = weightedSum / totalWeight;

      if (this.strictMode) {
        report.score = minScore;
      } else {
        const alpha = 0.7;
        const beta = 0.3;
        report.score = alpha * avgScore + beta * minScore;
      }
    } else {
      report.score = minScore;
    }

    // Adjust weight
    if (report.pruned) {
      report.adjustedWeight = Infinity;
      this.pruned++;
    } else {
      this.accepted++;
      // Raw default weight = 1.0
      report.adjustedWeight = edgeWeight / Math.max(report.score, 0.001);
    }

    // Cache result
    this.cacheMessage(cacheKey, report);

    return report;
  }

  // Individual check evaluation
  private evaluateCheck(
    checkName: CheckName,
    msg: any,
    context: ConsistencyReport
  ): CheckResult {
    switch (checkName) {
      case CheckName.Harmless:
        return this.checkHarmless(msg, context);
      case CheckName.ParadoxFree:
        return this.checkParadoxFree(msg, context);
      case CheckName.EntropySafe:
        return this.checkEntropySafe(msg);
      case CheckName.Coherent:
        return this.checkCoherent(msg);
      case CheckName.ZKValid:
        return this.checkZKValid(msg);
      case CheckName.QuantumTime:
        return this.checkQuantumTime(msg, context);
      case CheckName.SolarCoherence:
        return this.checkSolarCoherence(msg);
      case CheckName.GalacticAuth:
        return this.checkGalacticAuth(msg);
    }
  }

  // =========================================================================
  // CHECK 1: Harmless
  // =========================================================================
  private checkHarmless(
    msg: any,
    context: ConsistencyReport
  ): CheckResult {
    const violations: string[] = [];

    // Self-loop
    if (msg.sender === msg.receiver) {
      violations.push('self_loop');
      return { check: CheckName.Harmless, score: SCORE_ZERO, violations };
    }

    return { check: CheckName.Harmless, score: SCORE_ONE, violations };
  }

  // =========================================================================
  // CHECK 2: Paradox-Free
  // =========================================================================
  private checkParadoxFree(
    msg: any,
    context: ConsistencyReport
  ): CheckResult {
    const violations: string[] = [];

    // Temporal paradox
    if (msg.sourceTs > msg.targetTs) {
      violations.push('temporal_paradox');
      return {
        check: CheckName.ParadoxFree,
        score: 0.05,
        violations,
      };
    }

    // Future temporal consistency check (simplified)
    const now = Date.now() * 1_000_000; // nanos
    if (msg.targetTs > now + 1000 * 10_000_000) { // 10000 seconds in future
      violations.push('temporal_future_excessive');
      return {
        check: CheckName.ParadoxFree,
        score: 0.2,
        violations,
      };
    }

    return { check: CheckName.ParadoxFree, score: SCORE_ONE, violations };
  }

  // =========================================================================
  // CHECK 3: Entropy-Safe
  // =========================================================================
  private checkEntropySafe(msg: any): CheckResult {
    const maxSize = 10 * 1024 * 1024; // 10MB

    if (!msg.content && !msg.payload) {
      return { check: CheckName.EntropySafe, score: 0.5, violations: [] };
    }

    const size = (msg.content?.length || 0) + (msg.payload?.length || 0);
    if (size > maxSize) {
      const ratio = size / maxSize;
      return {
        check: CheckName.EntropySafe,
        score: Math.max(0, 1.0 - ratio / 10),
        violations: ['excessive_payload'],
      };
    }

    return { check: CheckName.EntropySafe, score: SCORE_ONE, violations: [] };
  }

  // =========================================================================
  // CHECK 4: Coherent
  // =========================================================================
  private checkCoherent(msg: any): CheckResult {
    const now = Date.now();
    const sourceTime = msg.sourceTs / 1_000_000; // Convert nanos to ms
    const age = now - sourceTime;
    const maxAge = 100 * 10_000; // 100 blocks × 10000 ms

    if (age > maxAge) {
      return {
        check: CheckName.Coherent,
        score: Math.max(0, 0.5 - age / (1_000_000)),
        violations: ['stale_message'],
      };
    }

    return { check: CheckName.Coherent, score: SCORE_ONE, violations: [] };
  }

  // =========================================================================
  // CHECK 5: ZK Valid
  // =========================================================================
  private checkZKValid(msg: any): CheckResult {
    if (!msg.zkProof || msg.zkProof.length === 0) {
      return {
        check: CheckName.ZKValid,
        score: 0.8,
        violations: [],
      };
    }
    return { check: CheckName.ZKValid, score: SCORE_ONE, violations: [] };
  }

  // =========================================================================
  // CHECK 6: Quantum Time
  // =========================================================================
  private checkQuantumTime(
    msg: any,
    context: ConsistencyReport
  ): CheckResult {
    const toleranceNs = 100; // 100ns tolerance
    const delta = msg.targetTs - msg.sourceTs;

    if (delta < 0) {
      return {
        check: CheckName.QuantumTime,
        score: 0.1,
        violations: ['retrocausality'],
      };
    }

    if (delta > toleranceNs * 1000) {
      return {
        check: CheckName.QuantumTime,
        score: 0.5,
        violations: [],
      };
    }

    return { check: CheckName.QuantumTime, score: SCORE_ONE, violations: [] };
  }

  // =========================================================================
  // CHECK 7: Solar Coherence
  // =========================================================================
  private checkSolarCoherence(msg: any): CheckResult {
    // Dummy solar coherence logic
    return { check: CheckName.SolarCoherence, score: SCORE_ONE, violations: [] };
  }

  // =========================================================================
  // CHECK 8: Galactic Auth
  // =========================================================================
  private checkGalacticAuth(msg: any): CheckResult {
    // Distributed ledger check (simplified)
    return { check: CheckName.GalacticAuth, score: SCORE_ONE, violations: [] };
  }

  // === HELPERS ===

  private getThreshold(check: CheckName): Score {
    return (this.thresholds as any)[check] ?? 0.5;
  }

  private getWeight(check: CheckName): number {
    return this.weights[check] ?? 1.0;
  }

  private isParadoxCheck(check: CheckName, result: CheckResult): boolean {
    return check === CheckName.ParadoxFree && result.score < 0.5;
  }

  private computeCacheKey(msg: any): string {
    return `${msg.sender}:${msg.sourceTs}:${msg.targetTs}:${msg.content?.slice(0, 64)}`;
  }

  private cacheMessage(key: string, report: ConsistencyReport): void {
    if (this.messageCache.size >= this.cacheMaxSize) {
      // Evict first entry
      const firstKey = this.messageCache.keys().next().value;
      if (firstKey) this.messageCache.delete(firstKey);
    }
    this.messageCache.set(key, report);
  }

  // === HEYTING ALGEBRA OPERATIONS ===

  /** Meet (∧): bottleneck */
  public static meet(a: Score, b: Score): Score {
    return Math.min(a, b);
  }

  /** Join (∨): coverage */
  public static join(a: Score, b: Score): Score {
    return Math.max(a, b);
  }

  /**
   * Implication (→): the core Heyting operation
   * p → q = (p ≤ q) ? 1 : q
   *
   * Semantics: "if p then q"
   * - If p ≤ q (p is weaker than q), knowing p implies q trivially
   * - Otherwise, implication equals q (the best we can say)
   */
  public static implication(p: Score, q: Score): Score {
    return p <= q ? SCORE_ONE : q;
  }

  /** Negation (¬): ¬p = p → ⊥ */
  public static negation(p: Score): Score {
    return this.implication(p, SCORE_ZERO);
  }

  /** Biconditional: p ↔ q = (p → q) ∧ (q → p) */
  public static biconditional(p: Score, q: Score): Score {
    return this.meet(
      this.implication(p, q),
      this.implication(q, p)
    );
  }
}

// Export singleton for use across modules
export const ARKHEOracle = TemporalConsistencyOracle.getInstance();
