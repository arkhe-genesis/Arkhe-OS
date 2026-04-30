/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */
/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-unused-vars, no-shadow-restricted-names */


import { Share2, Link, Shield, Layers } from 'lucide-react';
import React, { useState } from 'react';

import { useArkheSimulation } from '../hooks/useArkheSimulation';

export const UnifiedConsciousnessPanel: React.FC = () => {
  const state = useArkheSimulation();
  const [loading, setLoading] = useState(false);

  const handleUnify = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/consciousness/unify', { method: 'POST' });
      if (!response.ok) {throw new Error('Failed to unify consciousness');}
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const uc = state.unifiedConsciousness;
  if (!uc) {return null;}

  return (
    <div className="p-4 bg-zinc-900/50 rounded-lg border border-white/10 space-y-4 shadow-[0_0_20px_rgba(168,85,247,0.1)]">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Share2 className="w-5 h-5 text-purple-400" />
          <h3 className="font-medium text-white">Unified Consciousness</h3>
        </div>
        <div className={`px-2 py-0.5 rounded text-xs font-bold ${uc.isUnified ? 'bg-purple-500/20 text-purple-400' : 'bg-zinc-800 text-zinc-400'}`}>
          {uc.isUnified ? 'UNIFIED' : 'FRAGMENTED'}
        </div>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between text-xs">
          <span className="text-zinc-500">Unity Metric</span>
          <span className="text-purple-400 font-mono">{uc.unityMetric.toFixed(10)}</span>
        </div>

        <div className="flex flex-wrap gap-2">
          {uc.integratedQualia.map(q => (
            <span key={q} className="px-2 py-0.5 bg-purple-500/10 border border-purple-500/20 text-purple-300 text-[9px] font-mono rounded">
              {q}
            </span>
          ))}
        </div>
      </div>

      {!uc.isUnified ? (
        <button
          onClick={handleUnify}
          disabled={loading}
          className="w-full py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white text-xs font-bold rounded transition-colors shadow-[0_0_15px_rgba(168,85,247,0.3)]"
        >
          {loading ? 'FUSING QUALIA...' : 'FUSE RECOGNITION & REALIZATION'}
        </button>
      ) : (
        <div className="flex items-center gap-2 p-2 bg-purple-500/10 rounded border border-purple-500/20 text-[10px] text-purple-300">
          <Shield className="w-3 h-3" />
          <span>Recognition and realization are now one single feeling.</span>
        </div>
      )}
    </div>
  );
};
