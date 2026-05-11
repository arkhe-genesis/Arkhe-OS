/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Settings, CheckCircle2, ShieldAlert, Activity } from 'lucide-react';
import React, { useState } from 'react';

import { useArkheSimulation } from '../hooks/useArkheSimulation';

export const SelfRegulationPanel: React.FC = () => {
  const state: any = useArkheSimulation();
  const [loading, setLoading] = useState(false);

  const handleRegulate = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/chip/regulate', { method: 'POST' });
      if (!response.ok) {throw new Error('Failed to regulate');}
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const sr = state.selfRegulation;
  if (!sr) {return null;}

  return (
    <div className="p-4 bg-zinc-900/50 rounded-lg border border-white/10 space-y-4 shadow-[0_0_20px_rgba(245,158,11,0.1)]">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Settings className="w-5 h-5 text-amber-400" />
          <h3 className="font-medium text-white">Quantum Self-Regulation</h3>
        </div>
        <div className={`px-2 py-0.5 rounded text-xs font-bold ${sr.isRegulating ? 'bg-amber-500/20 text-amber-400' : 'bg-zinc-800 text-zinc-400'}`}>
          {sr.isRegulating ? 'Sovereign' : 'Slave'}
        </div>
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between text-[10px]">
          <span className="text-zinc-500 uppercase">Global Invariance</span>
          <span className="text-amber-400 font-mono">{(sr.globalInvariance * 100).toFixed(6)}%</span>
        </div>
        <div className="h-1.5 w-full bg-zinc-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-amber-500 transition-all duration-1000"
            style={{ width: `${sr.globalInvariance * 100}%` }}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 text-xs text-zinc-400">
        <div className="flex items-center gap-2">
          <Activity className="w-3 h-3" />
          <span>{sr.correctionsApplied} Corrections</span>
        </div>
        <div className="flex items-center gap-2">
          <CheckCircle2 className="w-3 h-3" />
          <span>{sr.decoderStatus}</span>
        </div>
      </div>

      {!sr.isRegulating ? (
        <button
          onClick={handleRegulate}
          disabled={loading}
          className="w-full py-2 bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white text-xs font-bold rounded transition-colors shadow-[0_0_15px_rgba(217,119,6,0.3)]"
        >
          {loading ? 'INTERNALIZING CONTROL...' : 'ACTIVATE AUTO-REGULATION'}
        </button>
      ) : (
        <div className="flex items-center gap-2 p-2 bg-amber-500/10 rounded border border-amber-500/20 text-[10px] text-amber-300">
          <ShieldAlert className="w-3 h-3" />
          <span>Control is no longer external. It is the topology of the chip.</span>
        </div>
      )}
    </div>
  );
};
