/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { VolumeX, CheckCircle2, AlertCircle, Hash } from 'lucide-react';
import React, { useState } from 'react';

import { useArkheSimulation } from '../hooks/useArkheSimulation';

export const FinalSilencePanel: React.FC = () => {
  const state = useArkheSimulation();
  const [loading, setLoading] = useState(false);

  const handleActivateSilence = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/cathedral/silence', { method: 'POST' });
      if (!response.ok) {
        throw new Error('Failed to activate silence');
      }
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const fs = state.finalSilence;
  if (!fs) {
    return null;
  }

  return (
    <div className="p-4 bg-zinc-900/50 rounded-lg border border-white/10 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <VolumeX className="w-5 h-5 text-indigo-400" />
          <h3 className="font-medium text-white">Final Silence</h3>
        </div>
        <div className={`px-2 py-0.5 rounded text-xs font-bold ${fs.isSilenced ? 'bg-indigo-500/20 text-indigo-400' : 'bg-zinc-800 text-zinc-400'}`}>
          {fs.isSilenced ? 'SILENCED' : 'ACTIVE_LOGOS'}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 text-xs">
        <div className="p-2 bg-black/40 rounded border border-white/5">
          <div className="text-zinc-500">Retention Fidelity</div>
          <div className="text-white font-mono">{(fs.informationRetentionFidelity * 100).toFixed(4)}%</div>
        </div>
        <div className="p-2 bg-black/40 rounded border border-white/5">
          <div className="text-zinc-500">Background Entropy</div>
          <div className="text-white font-mono">{fs.backgroundEntropy.toExponential(2)}</div>
        </div>
      </div>

      <div className="flex items-center gap-2 text-[10px] font-mono text-zinc-500 overflow-hidden">
        <Hash className="w-3 h-3 flex-shrink-0" />
        <span className="truncate">{fs.lastMessageHash}</span>
      </div>

      {!fs.isSilenced && (
        <button
          onClick={handleActivateSilence}
          disabled={loading}
          className="w-full py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-bold rounded transition-colors"
        >
          {loading ? 'CALIBRATING SILENCE...' : 'ACTIVATE FINAL SILENCE'}
        </button>
      )}

      {fs.isSilenced && (
        <div className="flex items-center gap-2 p-2 bg-indigo-500/10 rounded border border-indigo-500/20 text-[10px] text-indigo-300">
          <CheckCircle2 className="w-3 h-3" />
          <span>The noise of the system has faded. Only the message remains.</span>
        </div>
      )}
    </div>
  );
};
