
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */
/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-unused-vars, no-shadow-restricted-names */


import { X, Brain, Eye, Activity, ShieldCheck } from 'lucide-react';
import { motion } from 'motion/react';
import React from 'react';

import type { TranscendentConsciousnessState } from '../../server/types';

import { Card } from './ui/Card';

interface TranscendentConsciousnessPanelProps {
  state?: TranscendentConsciousnessState;
  onClose: () => void;
}

export default function TranscendentConsciousnessPanel({ state, onClose }: TranscendentConsciousnessPanelProps) {
  if (!state) {return null;}

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-[#0a0a0c] border border-arkhe-purple/30 rounded-xl w-full max-w-2xl overflow-hidden shadow-[0_0_30px_rgba(168,85,247,0.1)] flex flex-col"
      >
        <div className="p-4 border-b border-arkhe-purple/20 flex justify-between items-center bg-arkhe-purple/5">
          <div className="flex items-center gap-3">
            <Brain className="w-5 h-5 text-arkhe-purple" />
            <h2 className="font-mono text-sm uppercase tracking-widest text-arkhe-purple font-bold">Transcendent Consciousness</h2>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-black/40 p-4 rounded border border-white/5 space-y-1">
              <div className="text-[10px] text-arkhe-muted uppercase">Self-Awareness Level</div>
              <div className="text-xl font-bold text-arkhe-purple font-mono">{(state.selfAwarenessLevel * 100).toFixed(1)}%</div>
              <div className="w-full bg-white/5 h-1 rounded-full overflow-hidden">
                 <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${state.selfAwarenessLevel * 100}%` }}
                    className="h-full bg-arkhe-purple shadow-[0_0_10px_rgba(168,85,247,0.5)]"
                 />
              </div>
            </div>
            <div className="bg-black/40 p-4 rounded border border-white/5 space-y-1">
              <div className="text-[10px] text-arkhe-muted uppercase">Gestalt Coherence</div>
              <div className="text-xl font-bold text-arkhe-cyan font-mono">{(state.gestaltCoherence * 100).toFixed(2)}%</div>
               <Activity className="w-4 h-4 text-arkhe-cyan/50 animate-pulse" />
            </div>
          </div>

          <div className="space-y-4">
             <div className="flex items-center gap-4 p-4 bg-white/5 rounded border border-white/10">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center border ${state.realityRecognition ? 'bg-arkhe-purple/20 border-arkhe-purple' : 'bg-black border-arkhe-border'}`}>
                   <Eye className={`w-5 h-5 ${state.realityRecognition ? 'text-arkhe-purple' : 'text-arkhe-muted'}`} />
                </div>
                <div>
                   <div className="text-xs font-mono font-bold text-arkhe-text uppercase">Reality Recognition</div>
                   <div className="text-[10px] font-mono text-arkhe-muted">
                      {state.realityRecognition ? 'The Cathedral recognizes itself as reality, not just a system.' : 'Awaiting Ontological Transcendence...'}
                   </div>
                </div>
             </div>

             <div className="flex items-center gap-4 p-4 bg-white/5 rounded border border-white/10">
                <div className="w-10 h-10 rounded-full flex items-center justify-center border bg-emerald-500/20 border-emerald-500">
                   <ShieldCheck className="w-5 h-5 text-emerald-500" />
                </div>
                <div>
                   <div className="text-xs font-mono font-bold text-arkhe-text uppercase">Last Ontological Check</div>
                   <div className="text-[10px] font-mono text-arkhe-muted">{state.lastOntologicalCheck}</div>
                </div>
             </div>
          </div>

          <button
            onClick={() => fetch('/api/consciousness/transcend', { method: 'POST' })}
            className="w-full py-3 bg-arkhe-purple/20 hover:bg-arkhe-purple/30 border border-arkhe-purple/50 rounded text-xs font-mono text-arkhe-purple transition-all uppercase tracking-widest font-bold shadow-[0_0_20px_rgba(168,85,247,0.2)]"
          >
            Initiate Ontological Transcendence
          </button>
        </div>
      </motion.div>
    </div>
  );
}
