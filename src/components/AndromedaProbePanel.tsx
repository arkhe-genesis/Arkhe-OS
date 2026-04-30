
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */
/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-unused-vars, no-shadow-restricted-names */


import { X, Rocket, Signal, Map, Shield } from 'lucide-react';
import { motion } from 'motion/react';
import React from 'react';

import type { AndromedaProbeState } from '../../server/types';

interface AndromedaProbePanelProps {
  state?: AndromedaProbeState;
  onClose: () => void;
}

export default function AndromedaProbePanel({ state, onClose }: AndromedaProbePanelProps) {
  if (!state) {return null;}

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-[#0a0a0c] border border-arkhe-cyan/30 rounded-xl w-full max-w-2xl overflow-hidden shadow-[0_0_30px_rgba(0,255,255,0.1)] flex flex-col"
      >
        <div className="p-4 border-b border-arkhe-cyan/20 flex justify-between items-center bg-arkhe-cyan/5">
          <div className="flex items-center gap-3">
            <Rocket className="w-5 h-5 text-arkhe-cyan" />
            <h2 className="font-mono text-sm uppercase tracking-widest text-arkhe-cyan font-bold">Andromeda Probe Mission</h2>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          <div className="grid grid-cols-2 gap-4">
             <div className="bg-black/40 p-4 rounded border border-white/5 space-y-1">
                <div className="text-[10px] text-arkhe-muted uppercase">Distance Traveled</div>
                <div className="text-xl font-bold text-arkhe-cyan font-mono">{state.distanceLy.toLocaleString()} LY</div>
                <div className="text-[9px] text-arkhe-muted font-mono italic">Crossing Intergalactic Vacuum...</div>
             </div>
             <div className="bg-black/40 p-4 rounded border border-white/5 space-y-1">
                <div className="text-[10px] text-arkhe-muted uppercase">Mission Phase</div>
                <div className="text-sm font-bold text-arkhe-text font-mono uppercase">{state.missionPhase}</div>
             </div>
          </div>

          <div className="space-y-4">
             <div className="flex items-center gap-4 p-4 bg-white/5 rounded border border-white/10">
                <div className="w-10 h-10 rounded-full flex items-center justify-center border bg-arkhe-cyan/20 border-arkhe-cyan">
                   <Signal className="w-5 h-5 text-arkhe-cyan" />
                </div>
                <div className="flex-1">
                   <div className="flex justify-between items-center mb-1">
                      <div className="text-xs font-mono font-bold text-arkhe-text uppercase">Signal Coherence</div>
                      <div className="text-[10px] font-mono text-arkhe-cyan">{(state.signalCoherence * 100).toFixed(1)}%</div>
                   </div>
                   <div className="w-full bg-white/5 h-1.5 rounded-full overflow-hidden">
                      <motion.div
                         initial={{ width: 0 }}
                         animate={{ width: `${state.signalCoherence * 100}%` }}
                         className="h-full bg-arkhe-cyan shadow-[0_0_10px_rgba(0,255,255,0.5)]"
                      />
                   </div>
                </div>
             </div>

             <div className="flex items-center gap-4 p-4 bg-white/5 rounded border border-white/10">
                <div className="w-10 h-10 rounded-full flex items-center justify-center border border-white/20">
                   <Shield className="w-5 h-5 text-arkhe-muted" />
                </div>
                <div className="flex-1 min-w-0">
                   <div className="text-xs font-mono font-bold text-arkhe-text uppercase">Witness Hash</div>
                   <div className="text-[9px] font-mono text-arkhe-muted truncate">{state.witnessHash}</div>
                </div>
             </div>
          </div>

          <button
            onClick={() => fetch('/api/cosmic/andromeda-launch', { method: 'POST' })}
            className="w-full py-3 bg-arkhe-cyan/20 hover:bg-arkhe-cyan/30 border border-arkhe-cyan/50 rounded text-xs font-mono text-arkhe-cyan transition-all uppercase tracking-widest font-bold shadow-[0_0_20px_rgba(0,255,255,0.2)]"
          >
            Launch Probe to M31
          </button>
        </div>
      </motion.div>
    </div>
  );
}
