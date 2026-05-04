
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

// arkhe-dashboard/src/components/retrocausality/RetrocausalWisdomPanel.tsx
'use client';

import { useState, useEffect } from 'react';

import { retrocausalWisdomEcho } from '@/lib/retrocausality/retrocausalWisdomEcho';
import { EthicalPrinciple } from '@/types/ethics';

export default function RetrocausalWisdomPanel() {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [dashboard, setDashboard] = useState<any>(null);

  useEffect(() => {
    setDashboard(retrocausalWisdomEcho.getRetrocausalDashboard());
  }, []);

  const triggerEcho = async () => {
    await retrocausalWisdomEcho.generateRetrocausalEcho({
      insightId: `ins_${Date.now()}`,
      learnerId: 'learner_42',
      principle: EthicalPrinciple.COHERENCE_PRESERVATION,
      content: 'True stability requires accepting the non-linear flow of Ω.',
      coherenceScore: 0.98,
      noveltyScore: 0.85,
      timestamp_ns: Date.now() * 1e6
    }, (Date.now() - 3600000) * 1e6); // 1 hour ago

    setDashboard(retrocausalWisdomEcho.getRetrocausalDashboard());
  };

  return (
    <div className="bg-black/30 rounded-2xl border border-purple-500/20 p-4">
      <h3 className="text-xs font-bold text-purple-400 mb-3 tracking-widest uppercase flex items-center gap-2">
        <span>🌌🧠</span> Retrocausal Wisdom Echo
      </h3>

      {dashboard && (
        <div className="space-y-4">
          <div className="flex justify-between items-center bg-purple-500/10 p-3 rounded-xl border border-purple-500/30">
            <div>
              <p className="text-[9px] text-purple-300 font-bold uppercase tracking-tighter">Causal Loops</p>
              <p className="text-lg font-mono text-white">{dashboard.causalLoopsDetected}</p>
            </div>
            <div className="text-right">
              <p className="text-[9px] text-purple-300 font-bold uppercase tracking-tighter">Avg Resonance</p>
              <p className="text-lg font-mono text-emerald-400">{(dashboard.avgResonance * 100).toFixed(1)}%</p>
            </div>
          </div>

          <div className="space-y-2">
            <p className="text-[8px] text-slate-500 font-bold uppercase tracking-widest">Active Echos</p>
            {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
            {dashboard.recentEchoes.map((e: any) => (
              <div key={e.echoId} className="p-2 bg-white/5 rounded border border-white/5">
                <p className="text-[9px] text-white line-clamp-1 font-medium">{e.wisdomContent}</p>
                <div className="flex justify-between mt-1">
                  <span className="text-[7px] text-purple-400 font-mono">RES: {(e.resonanceAmplitude * 100).toFixed(1)}%</span>
                  {e.causalLoopClosed && <span className="text-[7px] text-emerald-400 font-bold">LOOP CLOSED</span>}
                </div>
              </div>
            ))}
            {dashboard.recentEchoes.length === 0 && (
              <p className="text-[9px] text-slate-600 italic">No historical resonances detected...</p>
            )}
          </div>

          <button
            onClick={triggerEcho}
            className="w-full py-2 bg-purple-600/20 border border-purple-500/40 text-purple-300 rounded-lg text-[10px] font-black hover:bg-purple-600/30 transition-all"
          >
            SENSE FUTURE GUIDANCE
          </button>
        </div>
      )}
    </div>
  );
}
