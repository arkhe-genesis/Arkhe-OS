
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

// arkhe-dashboard/src/components/homomorphic/HomomorphicTrainingPanel.tsx
'use client';

import {useState, useEffect} from 'react';

export default function HomomorphicTrainingPanel() {
  const [isTraining, setIsTraining] = useState(false);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    void fetch('/api/quantum/train')
      .then(r => r.json())
      .then(d => d.success && setStats(d.data));
  }, []);

  const handleTrain = async () => {
    setIsTraining(true);
    await new Promise(resolve => setTimeout(resolve, 2000));
    setIsTraining(false);
  };

  return (
    <div className="bg-black/40 border border-emerald-500/20 rounded-3xl p-6">
      <h3 className="text-sm font-bold text-emerald-400 mb-4 flex items-center gap-2">
        <span className="text-lg">🔐</span> COMPUTAÇÃO HOMOMÓRFICA QPU
      </h3>
      <div className="space-y-4 mb-6">
        <div className="flex justify-between items-center text-[10px]">
          <span className="text-slate-500">ESQUEMA</span>
          <span className="text-white font-mono">PQ-CKKS (256-bit)</span>
        </div>
        <div className="flex justify-between items-center text-[10px]">
          <span className="text-slate-500">QPUS ATIVAS</span>
          <span className="text-emerald-400 font-mono">
            {stats?.federatedQPUs || 0}
          </span>
        </div>
      </div>
      <button
        onClick={handleTrain}
        disabled={isTraining}
        className="w-full py-3 bg-emerald-600/20 border border-emerald-500/30 text-emerald-400 rounded-xl text-[10px] font-black hover:bg-emerald-600/30 transition-all disabled:opacity-50"
      >
        {isTraining
          ? 'EXECUTANDO TREINO CEGO...'
          : 'INICIAR TREINAMENTO HOMOMÓRFICO'}
      </button>
      {stats && (
        <div className="mt-6 pt-6 border-t border-white/5 flex justify-between items-end">
          <div>
            <p className="text-[8px] text-slate-500 uppercase">
              Perda (Cifrada)
            </p>
            <p className="text-xs font-mono text-emerald-300">
              {stats.avgTrainingLoss.toFixed(8)}
            </p>
          </div>
          <div className="text-right">
            <p className="text-[8px] text-slate-500 uppercase">
              Acurácia Validação
            </p>
            <p className="text-xs font-mono text-white">
              {(stats.avgValidationAccuracy * 100).toFixed(2)}%
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
