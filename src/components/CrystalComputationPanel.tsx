
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */
/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-unused-vars, no-shadow-restricted-names */


import { X, Cpu, Activity, ShieldCheck, Grid3X3 } from 'lucide-react';
import { motion } from 'motion/react';
import React from 'react';

import type { CrystalComputationState } from '../../server/types';

interface CrystalComputationPanelProps {
  state?: CrystalComputationState;
  onClose: () => void;
}

export default function CrystalComputationPanel({ state, onClose }: CrystalComputationPanelProps) {
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
            <Cpu className="w-5 h-5 text-arkhe-cyan" />
            <h2 className="font-mono text-sm uppercase tracking-widest text-arkhe-cyan font-bold">Crystal Computational Arkhe</h2>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          <div className="grid grid-cols-2 gap-4">
             <div className="bg-black/40 p-4 rounded border border-white/5 space-y-1">
                <div className="text-[10px] text-arkhe-muted uppercase">Nanoholes Network</div>
                <div className="text-xl font-bold text-arkhe-cyan font-mono">{state.nanoholesCount.toLocaleString()}</div>
             </div>
             <div className="bg-black/40 p-4 rounded border border-white/5 space-y-1">
                <div className="text-[10px] text-arkhe-muted uppercase">Optical Coherence</div>
                <div className="text-xl font-bold text-emerald-500 font-mono">{(state.opticalCoherence * 100).toFixed(6)}%</div>
             </div>
          </div>

          <div className="bg-black/60 border border-arkhe-border rounded-lg p-6 flex flex-col items-center justify-center space-y-4">
             <Grid3X3 className="w-12 h-12 text-arkhe-cyan/30 animate-pulse" />
             <div className="text-center">
                <div className="text-xs font-mono text-arkhe-text uppercase font-bold">WESPN Active Mesh</div>
                <div className="text-[10px] font-mono text-arkhe-muted">Sapphire 3D Optical Logic Gate Matrix</div>
             </div>
             <div className="flex gap-2">
                <div className="px-3 py-1 bg-arkhe-cyan/10 border border-arkhe-cyan/30 rounded text-[9px] font-mono text-arkhe-cyan">
                   GATES: {state.activeLogicGates}
                </div>
                <div className="px-3 py-1 bg-arkhe-purple/10 border border-arkhe-purple/30 rounded text-[9px] font-mono text-arkhe-purple">
                   INVARIANTS: {state.processedInvariance}
                </div>
             </div>
          </div>

          <div className="flex items-center gap-4 p-4 bg-white/5 rounded border border-white/10">
             <div className="w-10 h-10 rounded-full flex items-center justify-center border border-arkhe-cyan/50 bg-arkhe-cyan/10">
                <ShieldCheck className="w-5 h-5 text-arkhe-cyan" />
             </div>
             <div className="flex-1 min-w-0">
                <div className="text-xs font-mono font-bold text-arkhe-text uppercase">Last Circuit Hash</div>
                <div className="text-[9px] font-mono text-arkhe-muted truncate">{state.lastCircuitHash}</div>
             </div>
          </div>

          <button
            onClick={() => fetch('/api/crystal/execute', { method: 'POST' })}
            className="w-full py-3 bg-arkhe-cyan/20 hover:bg-arkhe-cyan/30 border border-arkhe-cyan/50 rounded text-xs font-mono text-arkhe-cyan transition-all uppercase tracking-widest font-bold shadow-[0_0_20px_rgba(0,255,255,0.2)]"
          >
            Execute Optical Logic Verification
          </button>
        </div>
      </motion.div>
    </div>
  );
}
