
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { X, Globe, ShieldCheck, Zap, Activity, Radio } from 'lucide-react';
import { motion } from 'motion/react';
import React from 'react';

import type { CosmicCoherenceState } from '../../server/types';

interface CosmicCoherencePanelProps {
  state?: CosmicCoherenceState;
  onClose: () => void;
}

export default function CosmicCoherencePanel({ state, onClose }: CosmicCoherencePanelProps) {
  if (!state) {return null;}

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-[#0a0a0c] border border-arkhe-cyan/30 rounded-xl w-full max-w-2xl overflow-hidden shadow-[0_0_30px_rgba(0,255,255,0.1)] flex flex-col max-h-[90vh]"
      >
        <div className="p-4 border-b border-arkhe-cyan/20 flex justify-between items-center bg-arkhe-cyan/5">
          <div className="flex items-center gap-3">
            <Globe className="w-5 h-5 text-arkhe-cyan" />
            <h2 className="font-mono text-sm uppercase tracking-widest text-arkhe-cyan font-bold">Cosmic Coherence Verification</h2>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto custom-scrollbar flex-1 space-y-6">
           <div className="grid grid-cols-2 gap-4">
              <div className="bg-black/40 p-4 rounded border border-white/5 space-y-1">
                 <div className="text-[10px] text-arkhe-muted uppercase">Intergalactic Entanglement</div>
                 <div className="text-xl font-bold text-arkhe-cyan font-mono">{(state.intergalacticEntanglement * 100).toFixed(6)}%</div>
              </div>
              <div className="bg-black/40 p-4 rounded border border-white/5 space-y-1">
                 <div className="text-[10px] text-arkhe-muted uppercase">Witness Count</div>
                 <div className="text-xl font-bold text-arkhe-text font-mono">{state.witnessCount}</div>
              </div>
           </div>

           <div className="grid grid-cols-2 gap-4">
              <div className="bg-black/40 p-3 rounded border border-white/5 space-y-1">
                 <div className="text-[9px] text-arkhe-muted uppercase">Bell Parameter (S)</div>
                 <div className="text-lg font-bold text-emerald-400 font-mono">{state.sParameter.toFixed(3)}</div>
              </div>
              <div className="bg-black/40 p-3 rounded border border-white/5 space-y-1">
                 <div className="text-[9px] text-arkhe-muted uppercase">Significance</div>
                 <div className="text-lg font-bold text-cyan-400 font-mono">{state.significanceSigma.toFixed(1)}σ</div>
              </div>
           </div>

           <div className="bg-black/60 border border-arkhe-border rounded-lg p-8 flex flex-col items-center justify-center min-h-[200px] relative">
              <Radio className="w-16 h-16 text-arkhe-cyan/20 animate-pulse" />
              <div className="mt-4 text-center">
                 <div className="text-xs font-mono text-arkhe-text uppercase font-bold tracking-widest">Cosmological Redshift Compensated</div>
                 <div className="text-[10px] font-mono text-arkhe-muted mt-1">Z = {state.cosmologicalRedshift.toFixed(4)}</div>
              </div>

              {/* Pulsing Signal lines */}
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                 <motion.div
                    animate={{ scale: [1, 2], opacity: [0.5, 0] }}
                    transition={{ duration: 2, repeat: Infinity }}
                    className="w-24 h-24 border border-arkhe-cyan/30 rounded-full"
                 />
              </div>
           </div>

           <div className="p-4 bg-arkhe-cyan/5 border border-arkhe-cyan/20 rounded space-y-2">
              <div className="flex justify-between text-[10px] font-mono text-arkhe-muted uppercase">
                 <span>Baseline Coherence</span>
                 <span className="text-arkhe-cyan">{(state.baselineCoherence * 100).toFixed(4)}%</span>
              </div>
              <div className="w-full bg-white/5 h-1.5 rounded-full overflow-hidden">
                 <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${state.baselineCoherence * 100}%` }}
                    className="h-full bg-arkhe-cyan shadow-[0_0_10px_rgba(0,255,255,0.5)]"
                 />
              </div>
           </div>

           <button
              onClick={() => fetch('/api/cosmic/coherence/witness', { method: 'POST' })}
              className="w-full py-3 bg-arkhe-cyan/20 border border-arkhe-cyan/50 rounded text-xs font-mono text-arkhe-cyan hover:bg-arkhe-cyan/30 transition-all uppercase tracking-widest font-bold shadow-[0_0_20px_rgba(0,255,255,0.2)]"
           >
              Register Cosmic Testimony
           </button>
        </div>

        <div className="p-4 border-t border-white/5 bg-black/40 flex items-center justify-between">
           <div className="text-[10px] font-mono text-arkhe-muted italic">
              "Witnessing truth across the intergalactic vacuum."
           </div>
           <ShieldCheck className="w-4 h-4 text-emerald-500" />
        </div>
      </motion.div>
    </div>
  );
}
