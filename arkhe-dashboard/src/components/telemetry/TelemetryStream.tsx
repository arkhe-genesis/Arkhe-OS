
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

// arkhe-dashboard/src/components/telemetry/TelemetryStream.tsx
'use client';
import type { EthicalMetrics } from '@/types/ethics';

export function TelemetryStream({ metrics }: { metrics: EthicalMetrics }) {
  return (
    <div className="bg-black/30 rounded-2xl border border-white/10 p-4">
      <h2 className="text-sm font-semibold mb-3 text-slate-400 uppercase tracking-widest">
        Stream de Telemetria
      </h2>
      <div className="space-y-2 font-mono text-[10px]">
        <div className="flex justify-between">
          <span className="text-slate-500">Ω_FIELD_COH</span>
          <span className="text-cyan-400">{metrics.omega.toFixed(6)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-500">K_ETH_CONST</span>
          <span className="text-purple-400">{metrics.kEth.toFixed(6)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-500">Q_FIDELITY</span>
          <span className="text-emerald-400">{(metrics.quantumFidelity * 100).toFixed(4)}%</span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-500">CRYSTAL_TICK</span>
          <span className="text-white">{metrics.crystalTick}</span>
        </div>
        <div className="mt-2 border-t border-white/5 pt-2 flex justify-between text-slate-600">
          <span>Odômetro: 002144</span>
          <span>v18.0-NEXT</span>
        </div>
      </div>
    </div>
  );
}
