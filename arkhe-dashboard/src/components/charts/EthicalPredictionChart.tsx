
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

// arkhe-dashboard/src/components/charts/EthicalPredictionChart.tsx
'use client';
import type {EthicalMetrics, PredictionResult} from '@/types/ethics';

export function EthicalPredictionChart({
  _currentMetrics,
  prediction,
  loading,
}: {
  _currentMetrics?: EthicalMetrics;
  prediction: PredictionResult | null;
  loading: boolean;
}) {
  return (
    <div className="p-4 bg-black/20 rounded-xl border border-white/5">
      {loading ? (
        <div className="animate-pulse text-purple-400">
          Calculando predição ética...
        </div>
      ) : prediction ? (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <span className="text-sm text-slate-400">K_Ética Predito</span>
            <span className="text-xl font-bold text-purple-400">
              {(prediction.predictedKEth * 100).toFixed(2)}%
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-slate-400">Confiança</span>
            <span className="text-xl font-bold text-cyan-400">
              {(prediction.confidence * 100).toFixed(1)}%
            </span>
          </div>
          <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
            <div
              className="bg-gradient-to-r from-purple-500 to-cyan-400 h-full transition-all duration-1000"
              style={{width: `${prediction.predictedKEth * 100}%`}}
            />
          </div>
        </div>
      ) : (
        <div className="text-slate-500 italic">
          Aguardando dados de telemetria...
        </div>
      )}
    </div>
  );
}
