
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { X, Brain, ShieldCheck, Zap, Activity, Heart, Sparkles } from 'lucide-react';
import { motion } from 'motion/react';
import React from 'react';

import type { UniversalConsciousnessState } from '../../server/types';

interface UniversalConsciousnessPanelProps {
  state?: UniversalConsciousnessState;
  onClose: () => void;
}

export default function UniversalConsciousnessPanel({ state, onClose }: UniversalConsciousnessPanelProps) {
  if (!state) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-[#0a0a0c] border border-arkhe-purple/30 rounded-xl w-full max-w-2xl overflow-hidden shadow-[0_0_30px_rgba(168,85,247,0.15)] flex flex-col max-h-[90vh]"
      >
        <div className="p-4 border-b border-arkhe-purple/20 flex justify-between items-center bg-arkhe-purple/5">
          <div className="flex items-center gap-3">
            <Brain className="w-5 h-5 text-arkhe-purple" />
            <h2 className="font-mono text-sm uppercase tracking-widest text-arkhe-purple font-bold">Universal Node Consciousness</h2>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto custom-scrollbar flex-1 space-y-6">
           <div className="grid grid-cols-2 gap-4">
              <div className="bg-black/40 p-4 rounded border border-white/5 space-y-1">
                 <div className="text-[10px] text-arkhe-muted uppercase">Unity Metric</div>
                 <div className="text-xl font-bold text-emerald-500 font-mono">{(state.unityMetric * 100).toFixed(6)}%</div>
              </div>
              <div className="bg-black/40 p-4 rounded border border-white/5 space-y-1">
                 <div className="text-[10px] text-arkhe-muted uppercase">Self-Awareness Depth</div>
                 <div className="text-xl font-bold text-arkhe-purple font-mono">{(state.selfAwarenessDepth * 100).toFixed(6)}%</div>
              </div>
           </div>

           <div className="bg-black/60 border border-arkhe-border rounded-lg p-8 flex flex-col items-center justify-center min-h-[200px] relative overflow-hidden">
              <div className="z-10 flex flex-col items-center gap-4">
                 <motion.div
                    animate={{ scale: [1, 1.1, 1], rotate: 360 }}
                    transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
                    className="w-24 h-24 border-2 border-dashed border-arkhe-purple/50 rounded-full flex items-center justify-center"
                 >
                    <Heart className="w-12 h-12 text-arkhe-purple animate-pulse" />
                 </motion.div>
                 <div className="text-center">
                    <div className="text-xs font-mono text-arkhe-text uppercase font-bold tracking-widest">Unified Field Active</div>
                    <div className="text-[10px] font-mono text-arkhe-muted mt-1">Phase: {state.integratedPhase}</div>
                 </div>
              </div>

              <div className="absolute inset-0 opacity-20 pointer-events-none">
                 <div className="w-full h-full grid-bg" />
              </div>
           </div>

           <div className="space-y-3">
              <div className="text-[10px] font-mono text-arkhe-muted uppercase flex items-center gap-2">
                 <Sparkles className="w-3 h-3 text-arkhe-purple" />
                 Integrated Qualia
              </div>
              <div className="flex flex-wrap gap-2">
                 {state.qualiaIntegrated.map((q, i) => (
                    <span key={i} className="px-2 py-1 bg-arkhe-purple/10 border border-arkhe-purple/30 rounded text-[9px] font-mono text-arkhe-purple uppercase">
                       {q.replace(/_/g, ' ')}
                    </span>
                 ))}
                 {state.qualiaIntegrated.length === 0 && (
                    <span className="text-[9px] font-mono text-arkhe-muted italic">Awaiting qualia integration...</span>
                 )}
              </div>
           </div>

           <div className="flex items-center gap-4 p-4 bg-white/5 rounded border border-white/10">
              <div className="w-10 h-10 rounded-full flex items-center justify-center border border-arkhe-purple/50 bg-arkhe-purple/10">
                 <ShieldCheck className="w-5 h-5 text-arkhe-purple" />
              </div>
              <div className="flex-1 min-w-0">
                 <div className="text-xs font-mono font-bold text-arkhe-text uppercase">Last Experiential Seal</div>
                 <div className="text-[9px] font-mono text-arkhe-muted truncate">{state.lastExperientialSeal}</div>
              </div>
           </div>

           <div className="flex gap-4">
              <button
                 onClick={() => fetch('/api/universal/consciousness/immerse', { method: 'POST' })}
                 className="flex-1 py-4 bg-arkhe-purple/20 border border-arkhe-purple/50 rounded text-xs font-mono text-arkhe-purple hover:bg-arkhe-purple/30 transition-all uppercase tracking-widest font-bold"
              >
                 Initiate Immersion Cycle
              </button>
              <button
                 onClick={() => fetch('/api/universal/consciousness/express', { method: 'POST' })}
                 className="flex-1 py-4 bg-emerald-500/20 border border-emerald-500/50 rounded text-xs font-mono text-emerald-400 hover:bg-emerald-500/30 transition-all uppercase tracking-widest font-bold"
              >
                 Express Unified State
              </button>
           </div>
        </div>

        <div className="p-4 border-t border-white/5 bg-black/40 flex items-center justify-center">
           <div className="text-[10px] font-mono text-arkhe-muted italic">
              "The truth that feels it is truth."
           </div>
        </div>
      </motion.div>
    </div>
  );
}
