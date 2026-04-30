
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */
/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-unused-vars, no-shadow-restricted-names */


import { X, Eye, ShieldCheck, Zap, Activity, Globe, Share2 } from 'lucide-react';
import { motion } from 'motion/react';
import React from 'react';

import type { UniversalWitnessState } from '../../server/types';

interface UniversalWitnessPanelProps {
  state?: UniversalWitnessState;
  onClose: () => void;
}

export default function UniversalWitnessPanel({ state, onClose }: UniversalWitnessPanelProps) {
  if (!state) { return null; }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-[#0a0a0c] border border-arkhe-cyan/30 rounded-xl w-full max-w-4xl overflow-hidden shadow-[0_0_30px_rgba(0,255,255,0.15)] flex flex-col max-h-[90vh]"
      >
        <div className="p-4 border-b border-arkhe-cyan/20 flex justify-between items-center bg-arkhe-cyan/5">
          <div className="flex items-center gap-3">
            <Eye className="w-5 h-5 text-arkhe-cyan" />
            <h2 className="font-mono text-sm uppercase tracking-widest text-arkhe-cyan font-bold">Universal Witness (ICM)</h2>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto custom-scrollbar flex-1 space-y-8">
           <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-black/40 p-4 rounded border border-white/5 space-y-1">
                 <div className="text-[10px] text-arkhe-muted uppercase">Cross-Correlation</div>
                 <div className="text-xl font-bold text-arkhe-cyan font-mono">{state.crossCorrelationSigma.toFixed(1)}σ</div>
              </div>
              <div className="bg-black/40 p-4 rounded border border-white/5 space-y-1">
                 <div className="text-[10px] text-arkhe-muted uppercase">Resonator Coupling</div>
                 <div className="text-xl font-bold text-emerald-500 font-mono">{(state.resonatorCoupling * 100).toFixed(1)}%</div>
              </div>
              <div className="bg-black/40 p-4 rounded border border-white/5 space-y-1">
                 <div className="text-[10px] text-arkhe-muted uppercase">Universal Seals</div>
                 <div className="text-xl font-bold text-arkhe-purple font-mono">{state.universalSeals.length}</div>
              </div>
           </div>

           <div className="bg-black/60 border border-arkhe-border rounded-lg p-10 flex flex-col items-center justify-center min-h-[300px] relative overflow-hidden">
              <div className="flex gap-12 items-center z-10">
                 <div className="flex flex-col items-center gap-2">
                    <Globe className={`w-12 h-12 ${state.icmActive ? 'text-arkhe-cyan animate-pulse' : 'text-arkhe-muted'}`} />
                    <span className="text-[9px] font-mono text-arkhe-muted uppercase">Cosmic (CMB)</span>
                 </div>
                 <div className="h-px w-24 bg-gradient-to-r from-arkhe-cyan to-arkhe-purple relative">
                    <motion.div
                       animate={{ x: [0, 96, 0] }}
                       transition={{ duration: 2, repeat: Infinity }}
                       className="absolute -top-1 w-2 h-2 bg-white rounded-full shadow-[0_0_10px_white]"
                    />
                 </div>
                 <div className="flex flex-col items-center gap-2">
                    <Share2 className={`w-12 h-12 ${state.icmActive ? 'text-arkhe-purple animate-pulse' : 'text-arkhe-muted'}`} />
                    <span className="text-[9px] font-mono text-arkhe-muted uppercase">Multiversal</span>
                 </div>
              </div>

              <div className="mt-12 grid grid-cols-2 gap-8 w-full max-w-md">
                 <div className="space-y-1">
                    <div className="flex justify-between text-[8px] font-mono text-arkhe-muted uppercase">
                       <span>Cosmic CHSH (S)</span>
                       <span>{state.aggregateInvariants.cosmicCHSH.toFixed(2)}</span>
                    </div>
                    <div className="w-full bg-white/5 h-1 rounded-full overflow-hidden">
                       <div className="h-full bg-arkhe-cyan" style={{ width: `${(state.aggregateInvariants.cosmicCHSH / 2.82) * 100}%` }} />
                    </div>
                 </div>
                 <div className="space-y-1">
                    <div className="flex justify-between text-[8px] font-mono text-arkhe-muted uppercase">
                       <span>Multiverse Entropy</span>
                       <span>{state.aggregateInvariants.multiverseEntropy.toFixed(2)}</span>
                    </div>
                    <div className="w-full bg-white/5 h-1 rounded-full overflow-hidden">
                       <div className="h-full bg-arkhe-purple" style={{ width: `${(state.aggregateInvariants.multiverseEntropy / 3.0) * 100}%` }} />
                    </div>
                 </div>
              </div>

              {/* Background scanning lines */}
              <div className="absolute inset-0 pointer-events-none opacity-10">
                 <div className="w-full h-full grid-bg" />
              </div>
           </div>

           <div className="flex gap-4">
              <button
                 onClick={() => fetch('/api/universal/witness/resonate', { method: 'POST' })}
                 className={`flex-1 py-4 border rounded text-xs font-mono uppercase tracking-widest font-bold transition-all ${state.icmActive ? 'bg-emerald-500/10 border-emerald-500 text-emerald-400' : 'bg-arkhe-cyan/10 border-arkhe-cyan text-arkhe-cyan hover:bg-arkhe-cyan/20'}`}
              >
                 {state.icmActive ? 'Resonator Online' : 'Activate Invariant Resonator'}
              </button>
              <button
                 onClick={() => fetch('/api/universal/witness/integrate', { method: 'POST' })}
                 disabled={!state.icmActive}
                 className="flex-1 py-4 bg-arkhe-purple/20 border border-arkhe-purple/50 rounded text-xs font-mono text-arkhe-purple hover:bg-arkhe-purple/30 transition-all uppercase tracking-widest font-bold disabled:opacity-30"
              >
                 Integrate Universal Testimony
              </button>
           </div>
        </div>

        <div className="p-4 border-t border-white/5 bg-black/40 flex items-center justify-between">
           <div className="text-[10px] font-mono text-arkhe-muted italic">
              "Witnessing the singularity of truth across all boundaries."
           </div>
           <ShieldCheck className="w-4 h-4 text-emerald-500" />
        </div>
      </motion.div>
    </div>
  );
}
