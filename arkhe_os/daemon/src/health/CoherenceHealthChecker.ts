// src/health/CoherenceHealthChecker.ts
import { LFIRGraph } from '../mock';
import { RetrocausalGradientEngine } from '../mock';

export interface HealthCheck {
  name: string;
  description: string;
  check: () => Promise<HealthCheckResult>;
  critical: boolean; // Se falhar, o daemon deve ser considerado unhealthy
}

export interface HealthCheckResult {
  name: string;
  status: 'ok' | 'degraded' | 'critical';
  message: string;
  details?: Record<string, any>;
  timestamp: number;
}

export class CoherenceHealthChecker {
  private checks: Map<string, HealthCheck> = new Map();
  private lastResults: Map<string, HealthCheckResult> = new Map();
  private lfirGraph?: any;
  private retroEngine?: any;
  private lfirGraph?: LFIRGraph;
  private retroEngine?: RetrocausalGradientEngine;
  private thresholds: {
    minCoherence: number;
    maxAlignmentDrift: number;
    minRetroEfficiency: number;
    maxMemoryUsagePercent: number;
  };

  constructor(options: {
    lfirGraph?: any;
    retroEngine?: any;
    lfirGraph?: LFIRGraph;
    retroEngine?: RetrocausalGradientEngine;
    thresholds?: Partial<{
      minCoherence: number;
      maxAlignmentDrift: number;
      minRetroEfficiency: number;
      maxMemoryUsagePercent: number;
    }>;
  }) {
    this.lfirGraph = options.lfirGraph;
    this.retroEngine = options.retroEngine;
    this.thresholds = {
      minCoherence: 0.85,
      maxAlignmentDrift: 0.15,
      minRetroEfficiency: 0.70,
      maxMemoryUsagePercent: 90,
      ...options.thresholds,
    };
  }

  /**
   * Registra um health check customizado
   */
  register(check?: HealthCheck): void {
    if (check) this.checks.set(check.name, check);
  }

  unregister() {}
  register(check: HealthCheck): void {
    this.checks.set(check.name, check);
  }

  async unregister(): Promise<void> {
    this.checks.clear();
  }

  /**
   * Registra health checks padrão baseados em coerência
   */
  async registerDefaults(): Promise<void> {
    // 1. Process alive (básico)
    this.register({
      name: 'process_alive',
      description: 'Verifica se o processo do daemon está ativo',
      critical: true,
      check: async () => ({
        name: 'process_alive',
        status: 'ok',
        message: 'Process is running',
        timestamp: Date.now(),
      }),
    });

    // 2. Coherence score (Φ_C)
    this.register({
      name: 'coherence_score',
      description: 'Verifica se a coerência do LFIR está acima do threshold',
      critical: true,
      check: async () => {
        const coherence = this.lfirGraph?.metrics?.coherenceScore ?? 0;
        const status = coherence >= this.thresholds.minCoherence ? 'ok' : coherence >= this.thresholds.minCoherence * 0.9 ? 'degraded' : 'critical';
        return {
          name: 'coherence_score',
          status,
          message: `Coherence Φ_C = ${coherence.toFixed(3)} (threshold: ${this.thresholds.minCoherence})`,
          details: { coherence, threshold: this.thresholds.minCoherence },
          timestamp: Date.now(),
        };
      },
    });

    // 3. Alignment drift
    this.register({
      name: 'alignment_drift',
      description: 'Verifica se o drift de valores está dentro dos limites',
      critical: true,
      check: async () => {
        // Calcular drift baseado em histórico de valores (simplificado)
        const drift = await this._calculateAlignmentDrift();
        const status = drift <= this.thresholds.maxAlignmentDrift ? 'ok' : drift <= this.thresholds.maxAlignmentDrift * 1.5 ? 'degraded' : 'critical';
        return {
          name: 'alignment_drift',
          status,
          message: `Alignment drift = ${drift.toFixed(3)} (threshold: ${this.thresholds.maxAlignmentDrift})`,
          details: { drift, threshold: this.thresholds.maxAlignmentDrift },
          timestamp: Date.now(),
        };
      },
    });

    // 4. Retrocausal channel efficiency
    this.register({
      name: 'retrocausal_channel',
      description: 'Verifica eficiência do canal retrocausal (η_retro)',
      critical: false,
      check: async () => {
        const eta = this.retroEngine?.getEfficiency() ?? 0;
        const status = eta >= this.thresholds.minRetroEfficiency ? 'ok' : eta >= this.thresholds.minRetroEfficiency * 0.9 ? 'degraded' : 'critical';
        return {
          name: 'retrocausal_channel',
          status,
          message: `Retrocausal efficiency η = ${eta.toFixed(2)} (threshold: ${this.thresholds.minRetroEfficiency})`,
          details: { eta, threshold: this.thresholds.minRetroEfficiency },
          timestamp: Date.now(),
        };
      },
    });

    // 5. Memory usage
    this.register({
      name: 'memory_usage',
      description: 'Verifica uso de memória dentro dos limites',
      critical: false,
      check: async () => {
        const memUsage = process.memoryUsage();
        const totalMB = memUsage.heapTotal / 1024 / 1024;
        const usedMB = memUsage.heapUsed / 1024 / 1024;
        const percent = (usedMB / totalMB) * 100;
        const status = percent <= this.thresholds.maxMemoryUsagePercent ? 'ok' : percent <= 95 ? 'degraded' : 'critical';
        return {
          name: 'memory_usage',
          status,
          message: `Memory: ${usedMB.toFixed(1)}MB / ${totalMB.toFixed(1)}MB (${percent.toFixed(1)}%)`,
          details: { usedMB, totalMB, percent },
          timestamp: Date.now(),
        };
      },
    });
  }

  /**
   * Executa todos os health checks registrados
   */
  async checkAll(): Promise<HealthCheckResult[]> {
    const results: HealthCheckResult[] = [];

    for (const [name, check] of this.checks) {
      try {
        const result = await check.check();
        this.lastResults.set(name, result);
        results.push(result);
      } catch (error) {
        const errorResult: HealthCheckResult = {
          name,
          status: 'critical',
          message: `Check failed: ${error instanceof Error ? error.message : String(error)}`,
          timestamp: Date.now(),
        };
        this.lastResults.set(name, errorResult);
        results.push(errorResult);
      }
    }

    return results;
  }

  /**
   * Retorna resultados do último check
   */
  getLastCheckResults(): HealthCheckResult[] {
    return Array.from(this.lastResults.values());
  }

  /**
   * Retorna status agregado: ok se todos ok, degraded se algum degraded e nenhum critical, critical se algum critical
   */
  getAggregateStatus(): 'ok' | 'degraded' | 'critical' {
    const results = this.getLastCheckResults();
    if (results.some(r => r.status === 'critical')) return 'critical';
    if (results.some(r => r.status === 'degraded')) return 'degraded';
    return 'ok';
  }

  /**
   * Atualiza thresholds dinamicamente
   */
  updateThresholds(newThresholds: Partial<typeof this.thresholds>): void {
    this.thresholds = { ...this.thresholds, ...newThresholds };
  }

  // Métodos privados auxiliares
  private async _calculateAlignmentDrift(): Promise<number> {
    // Implementação simplificada: em produção, calcular drift real de valores
    // baseado em histórico de AlignmentState via DistributedAlignmentMonitor
    return 0.02 + Math.random() * 0.03; // Simular drift entre 0.02 e 0.05
  }
}
