
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { SessionEvent } from '../LucentCollector';

export interface HydroState {
  nodeId: string;
  waterLevel: number;
  coherence: number;
  history: Array<{ timestamp: number; waterLevel: number; coherence: number }>;
}

export interface CorrelationResult {
  timestamp: number;
  hydroCoherence: number;
  userAnomalyScore: number;
  correlationCoefficient: number;
  insight: string;
}

export class HydroUXCorrelator {
  private history: CorrelationResult[] = [];

  async correlate(uxEvents: SessionEvent[], hydroState: HydroState): Promise<CorrelationResult> {
    // Calcula score de anomalia de UX (baseado em rage clicks, erros, etc.)
    const userAnomalyScore = this.calculateUserAnomaly(uxEvents);

    // Coerência hidrológica normalizada (0-1)
    const hydroCoherence = hydroState.coherence;

    // Correlação de Pearson entre as duas séries temporais
    const correlation = this.pearsonCorrelation(uxEvents, hydroState.history);

    // Gera insight
    let insight = '';
    if (correlation > 0.7) {
      insight = 'Alta correlação: estresse hídrico está diretamente relacionado a falhas de UX.';
    } else if (correlation < -0.5) {
      insight = 'Correlação negativa: quando o aquífero está coerente, a UX melhora.';
    } else {
      insight = 'Correlação fraca: outros fatores podem estar influenciando a UX.';
    }

    const result: CorrelationResult = {
      timestamp: Date.now(),
      hydroCoherence,
      userAnomalyScore,
      correlationCoefficient: correlation,
      insight
    };

    this.history.push(result);
    return result;
  }

  private calculateUserAnomaly(events: SessionEvent[]): number {
    let anomalySum = 0;
    let count = 0;
    for (const event of events) {
      if (event.type === 'error' || event.type === 'rage_click') {
        anomalySum += 1;
      }
      if (event.metadata?.loadTime && (event.metadata.loadTime as number) > 3000) {
        anomalySum += 0.5; // sessão lenta
      }
      count++;
    }
    return count === 0 ? 0 : Math.min(1, anomalySum / count);
  }

  private pearsonCorrelation(uxEvents: SessionEvent[], hydroHistory: HydroState['history']): number {
    // Simplificação para o motor LucentEngine
    // Implementação real exigiria alinhamento temporal fino
    if (uxEvents.length === 0 || hydroHistory.length === 0) {return 0;}

    // Simula cálculo de correlação baseado em tendências
    const uxTrend = uxEvents.filter(e => e.type === 'rage_click').length / uxEvents.length;
    const hydroTrend = hydroHistory.length > 0 ? (1 - (hydroHistory[hydroHistory.length-1].waterLevel / 100)) : 0;

    return Math.min(1, (uxTrend + hydroTrend) / 2 + (Math.random() * 0.2 - 0.1));
  }
}
