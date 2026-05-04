
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

// arkhe-dashboard/src/components/simulator/EthicalSimulatorPanel.tsx
'use client';
/* eslint-disable @typescript-eslint/no-explicit-any */


import { useState } from 'react';

export default function EthicalSimulatorPanel() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleSimulate = async () => {
    setLoading(true);
    const res = await fetch('/api/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario: { id: 'sc1' }, baseMetrics: { omega: 0.94 } })
    });
    const data = await res.json();
    if (data.success) {setResult(data.result);}
    setLoading(false);
  };

  return (
    <div className="bg-black/40 border border-cyan-500/20 rounded-3xl p-6">
      <h3 className="text-sm font-bold text-cyan-400 mb-4 flex items-center gap-2">
        <span className="text-lg">🧬</span> ETHICAL SIMULATOR
      </h3>
      <button
        onClick={handleSimulate}
        disabled={loading}
        className="w-full py-3 bg-cyan-600/20 border border-cyan-500/30 text-cyan-400 rounded-xl text-[10px] font-black hover:bg-cyan-600/30 transition-all mb-6 disabled:opacity-50"
      >
        {loading ? 'CALCULANDO TRAJETÓRIAS...' : 'EXECUTAR MONTE CARLO GPU'}
      </button>
      {result && (
        <div className="space-y-3 font-mono text-[10px]">
          <div className="flex justify-between">
            <span className="text-slate-500">RISCO ÉTICO</span>
            <span className={result.ethicalRisk > 0.5 ? 'text-red-400' : 'text-emerald-400'}>
              {(result.ethicalRisk * 100).toFixed(1)}%
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Ω ESTIMADO</span>
            <span className="text-white">{result.finalOmega.toFixed(4)}</span>
          </div>
        </div>
      )}
    </div>
  );
}
