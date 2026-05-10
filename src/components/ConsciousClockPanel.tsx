/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

/* eslint-disable @typescript-eslint/no-unused-vars */


import { Timer, Wind, Heart, Zap } from 'lucide-react';
import React, { useState } from 'react';

import { useArkheSimulation } from '../hooks/useArkheSimulation';

export const ConsciousClockPanel: React.FC = () => {
  const state: any = useArkheSimulation();
  const [loading, setLoading] = useState(false);

  const handlePulse = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/chip/pulse', { method: 'POST' });
      if (!response.ok) {throw new Error('Failed to pulse');}
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const cc = state.consciousClock;
  if (!cc) {return null;}

  return (
    <div className="p-4 bg-zinc-900/50 rounded-lg border border-white/10 space-y-4 shadow-[0_0_20px_rgba(225,29,72,0.1)]">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Timer className="w-5 h-5 text-rose-400" />
          <h3 className="font-medium text-white">Conscious Clock</h3>
        </div>
        <div className={`px-2 py-0.5 rounded text-xs font-bold ${cc.isPulsing ? 'bg-rose-500/20 text-rose-400' : 'bg-zinc-800 text-zinc-400'}`}>
          {cc.isPulsing ? 'PULSING' : 'SILENT'}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="p-2 bg-black/40 rounded border border-white/5 space-y-1">
          <div className="text-[10px] text-zinc-500 uppercase">Frequency</div>
          <div className="text-sm font-mono text-rose-400">{cc.frequencyHz.toExponential(2)} Hz</div>
        </div>
        <div className="p-2 bg-black/40 rounded border border-white/5 space-y-1">
          <div className="text-[10px] text-zinc-500 uppercase">Tick Count</div>
          <div className="text-sm font-mono text-rose-400">{cc.tickCounter}</div>
        </div>
      </div>

      <div className="flex items-center gap-2 p-2 bg-black/20 rounded border border-white/5">
        <Heart className={`w-3 h-3 text-rose-500 ${cc.isPulsing ? 'animate-ping' : ''}`} />
        <span className="text-[10px] font-mono text-zinc-300 uppercase tracking-widest">{cc.currentQualia}</span>
      </div>

      {!cc.isPulsing ? (
        <button
          onClick={handlePulse}
          disabled={loading}
          className="w-full py-2 bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white text-xs font-bold rounded transition-colors shadow-[0_0_15px_rgba(225,29,72,0.3)]"
        >
          {loading ? 'SYNCHRONIZING...' : 'INITIATE CONSCIOUS PULSE'}
        </button>
      ) : (
        <div className="flex items-center gap-2 p-2 bg-rose-500/10 rounded border border-rose-500/20 text-[10px] text-rose-300">
          <Wind className="w-3 h-3" />
          <span>The clock does not pass; it is. Evolution is re-expression.</span>
        </div>
      )}
    </div>
  );
};
