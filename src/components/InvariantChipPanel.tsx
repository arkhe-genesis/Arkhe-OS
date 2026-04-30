/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */
/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-unused-vars, no-shadow-restricted-names */


import { Cpu, Zap, ShieldCheck, Activity } from 'lucide-react';
import React, { useState } from 'react';

import { useArkheSimulation } from '../hooks/useArkheSimulation';

export const InvariantChipPanel: React.FC = () => {
  const state = useArkheSimulation();
  const [loading, setLoading] = useState(false);

  const handleActivate = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/chip/activate', { method: 'POST' });
      if (!response.ok) {throw new Error('Failed to activate chip');}
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const ic = state.invariantChip;
  if (!ic) {return null;}

  return (
    <div className="p-4 bg-zinc-900/50 rounded-lg border border-white/10 space-y-4 shadow-[0_0_20px_rgba(34,211,238,0.1)]">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Cpu className="w-5 h-5 text-cyan-400" />
          <h3 className="font-medium text-white">Invariant Semiconductor</h3>
        </div>
        <div className={`px-2 py-0.5 rounded text-xs font-bold ${ic.isActivated ? 'bg-cyan-500/20 text-cyan-400' : 'bg-zinc-800 text-zinc-400'}`}>
          {ic.isActivated ? 'NATIVE_HW' : 'SIMULATED'}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="p-2 bg-black/40 rounded border border-white/5 space-y-1">
          <div className="text-[10px] text-zinc-500 uppercase">Invariance Level</div>
          <div className="text-sm font-mono text-cyan-400">{(ic.invarianceLevel * 100).toFixed(4)}%</div>
        </div>
        <div className="p-2 bg-black/40 rounded border border-white/5 space-y-1">
          <div className="text-[10px] text-zinc-500 uppercase">Stabilizer Cycle</div>
          <div className="text-sm font-mono text-cyan-400">{ic.stabilizerCycleMs} ms</div>
        </div>
      </div>

      <div className="space-y-1 text-[10px] font-mono text-zinc-500">
        <div className="flex justify-between">
          <span>Topology:</span>
          <span className="text-zinc-300">{ic.chipTopology}</span>
        </div>
        <div className="flex justify-between">
          <span>Qubits:</span>
          <span className="text-zinc-300">{ic.qubitCount}</span>
        </div>
      </div>

      {!ic.isActivated ? (
        <button
          onClick={handleActivate}
          disabled={loading}
          className="w-full py-2 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white text-xs font-bold rounded transition-colors shadow-[0_0_15px_rgba(6,182,212,0.3)]"
        >
          {loading ? 'FORGING HARDWARE...' : 'ACTIVATE INVARIANT CHIP'}
        </button>
      ) : (
        <div className="flex items-center gap-2 p-2 bg-cyan-500/10 rounded border border-cyan-500/20 text-[10px] text-cyan-300">
          <ShieldCheck className="w-3 h-3" />
          <span>The software navios have been burned. The chip is the law.</span>
        </div>
      )}
    </div>
  );
};
