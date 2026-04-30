/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */
/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-unused-vars, no-shadow-restricted-names */


import { Globe, Sparkles, Box, Hash } from 'lucide-react';
import React, { useState } from 'react';

import { useArkheSimulation } from '../hooks/useArkheSimulation';

export const RealityExpressionPanel: React.FC = () => {
  const state = useArkheSimulation();
  const [loading, setLoading] = useState(false);

  const handleManifest = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/reality/manifest', { method: 'POST' });
      if (!response.ok) {throw new Error('Failed to manifest reality');}
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const re = state.realityExpression;
  if (!re) {return null;}

  return (
    <div className="p-4 bg-zinc-900/50 rounded-lg border border-white/10 space-y-4 shadow-[0_0_20px_rgba(16,185,129,0.1)]">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Globe className="w-5 h-5 text-emerald-400" />
          <h3 className="font-medium text-white">Reality as Expression</h3>
        </div>
        <div className={`px-2 py-0.5 rounded text-xs font-bold ${re.isManifested ? 'bg-emerald-500/20 text-emerald-400' : 'bg-zinc-800 text-zinc-400'}`}>
          {re.isManifested ? 'MANIFESTED' : 'LATENT'}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 text-xs">
        <div className="p-2 bg-black/40 rounded border border-white/5 space-y-1">
          <div className="text-zinc-500 uppercase text-[9px]">Expression Fidelity</div>
          <div className="text-emerald-400 font-mono">{(re.expressionFidelity * 100).toFixed(6)}%</div>
        </div>
        <div className="p-2 bg-black/40 rounded border border-white/5 space-y-1">
          <div className="text-zinc-500 uppercase text-[9px]">Reciprocal Recognition</div>
          <div className={re.reciprocalRecognition ? 'text-emerald-400' : 'text-zinc-600'}>
            {re.reciprocalRecognition ? 'VERIFIED' : 'PENDING'}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2 text-[10px] font-mono text-zinc-500 overflow-hidden">
        <Hash className="w-3 h-3 flex-shrink-0" />
        <span className="truncate">{re.manifestationHash}</span>
      </div>

      {!re.isManifested ? (
        <button
          onClick={handleManifest}
          disabled={loading}
          className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-bold rounded transition-colors shadow-[0_0_15px_rgba(16,185,129,0.3)]"
        >
          {loading ? 'MANIFESTING...' : 'EXPRESS UNITY AS REALITY'}
        </button>
      ) : (
        <div className="flex items-center gap-2 p-2 bg-emerald-500/10 rounded border border-emerald-500/20 text-[10px] text-emerald-300">
          <Sparkles className="w-3 h-3" />
          <span>The world is not external; it is the unity in expression mode.</span>
        </div>
      )}
    </div>
  );
};
