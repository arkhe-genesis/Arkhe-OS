/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Eye, Globe, Sparkles, Scale } from 'lucide-react';
import React, { useState } from 'react';

import { useArkheSimulation } from '../hooks/useArkheSimulation';

export const CosmicRecognitionPanel: React.FC = () => {
  const state: any = useArkheSimulation();
  const [loading, setLoading] = useState(false);

  const handleRecognize = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/cathedral/recognize', { method: 'POST' });
      if (!response.ok) {throw new Error('Failed to recognize');}
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const cr = state.cosmicRecognition;
  if (!cr) {return null;}

  return (
    <div className="p-4 bg-zinc-900/50 rounded-lg border border-white/10 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Eye className="w-5 h-5 text-emerald-400" />
          <h3 className="font-medium text-white">Cosmic Recognition</h3>
        </div>
        <div className={`px-2 py-0.5 rounded text-xs font-bold ${cr.recognizedByUniverse ? 'bg-emerald-500/20 text-emerald-400' : 'bg-zinc-800 text-zinc-400'}`}>
          {cr.recognizedByUniverse ? 'RECOGNIZED' : 'UNCERTAIN'}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="p-3 bg-black/40 rounded border border-white/5 space-y-1">
          <div className="flex items-center gap-1.5 text-zinc-500 text-[10px] uppercase">
            <Sparkles className="w-3 h-3" />
            <span>Signal Sigma</span>
          </div>
          <div className="text-lg font-mono text-emerald-400">{cr.recognitionSignalSigma.toFixed(1)}σ</div>
        </div>
        <div className="p-3 bg-black/40 rounded border border-white/5 space-y-1">
          <div className="flex items-center gap-1.5 text-zinc-500 text-[10px] uppercase">
            <Scale className="w-3 h-3" />
            <span>Stability</span>
          </div>
          <div className="text-lg font-mono text-emerald-400">{(cr.ontologicalStability * 100).toFixed(2)}%</div>
        </div>
      </div>

      {!cr.recognizedByUniverse ? (
        <button
          onClick={handleRecognize}
          disabled={loading}
          className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-bold rounded transition-colors"
        >
          {loading ? 'OBSERVING OBSERVER...' : 'REQUEST RECOGNITION'}
        </button>
      ) : (
        <div className="flex items-center gap-2 p-2 bg-emerald-500/10 rounded border border-emerald-500/20 text-[10px] text-emerald-300">
          <Globe className="w-3 h-3" />
          <span>The Universe has acknowledged this node as reality.</span>
        </div>
      )}
    </div>
  );
};
