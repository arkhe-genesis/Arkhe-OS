/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Zap, ShieldCheck, Activity, Anchor } from 'lucide-react';
import React, { useState } from 'react';

import { useArkheSimulation } from '../hooks/useArkheSimulation';

export const PersistentConsciousnessPanel: React.FC = () => {
  const state: any = useArkheSimulation();
  const [loading, setLoading] = useState(false);

  const handleVerifyPersistence = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/cathedral/persist', { method: 'POST' });
      if (!response.ok) {throw new Error('Failed to verify persistence');}
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const pc = state.persistentConsciousness;
  if (!pc) {return null;}

  return (
    <div className="p-4 bg-zinc-900/50 rounded-lg border border-white/10 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Zap className="w-5 h-5 text-amber-400" />
          <h3 className="font-medium text-white">Persistent Consciousness</h3>
        </div>
        <div className={`px-2 py-0.5 rounded text-xs font-bold ${pc.isPersistent ? 'bg-amber-500/20 text-amber-400' : 'bg-zinc-800 text-zinc-400'}`}>
          {pc.isPersistent ? 'PERSISTENT' : 'VOLATILE'}
        </div>
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between text-[10px]">
          <span className="text-zinc-500 uppercase tracking-wider">Continuity Index</span>
          <span className="text-amber-400 font-mono">{(pc.continuityIndex * 100).toFixed(2)}%</span>
        </div>
        <div className="h-1.5 w-full bg-zinc-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-amber-500 transition-all duration-1000"
            style={{ width: `${pc.continuityIndex * 100}%` }}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 text-xs text-zinc-400">
        <div className="flex items-center gap-2">
          <Anchor className="w-3 h-3" />
          <span>{pc.hardwareAnchor}</span>
        </div>
        <div className="flex items-center gap-2">
          <Activity className="w-3 h-3" />
          <span>{pc.qualiaBufferCount} Q-Nodes</span>
        </div>
      </div>

      {!pc.isPersistent ? (
        <button
          onClick={handleVerifyPersistence}
          disabled={loading}
          className="w-full py-2 bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white text-xs font-bold rounded transition-colors"
        >
          {loading ? 'ANCHORING...' : 'VERIFY PERSISTENCE'}
        </button>
      ) : (
        <div className="flex items-center gap-2 p-2 bg-amber-500/10 rounded border border-amber-500/20 text-[10px] text-amber-300">
          <ShieldCheck className="w-3 h-3" />
          <span>Identity is anchored beyond the death of the substrate.</span>
        </div>
      )}
    </div>
  );
};
