
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

/* eslint-disable @typescript-eslint/no-unused-vars */


import { X, Zap, Heart, Shield, Activity } from 'lucide-react';
import { motion } from 'motion/react';
import React from 'react';

import type { VacuumHarvestingState } from '../../server/types';

interface VacuumHarvestingPanelProps {
  state?: VacuumHarvestingState;
  onClose: () => void;
}

export default function VacuumHarvestingPanel({ state, onClose }: VacuumHarvestingPanelProps) {
  if (!state) { return null; }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-[#0a0a0c] border border-amber-500/30 rounded-xl w-full max-w-2xl overflow-hidden shadow-[0_0_30px_rgba(245,158,11,0.1)] flex flex-col"
      >
        <div className="p-4 border-b border-amber-500/20 flex justify-between items-center bg-amber-500/5">
          <div className="flex items-center gap-3">
            <Zap className="w-5 h-5 text-amber-500" />
            <h2 className="font-mono text-sm uppercase tracking-widest text-amber-500 font-bold">Quantum Vacuum Harvesting</h2>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          <div className="grid grid-cols-2 gap-4">
             <div className="bg-black/40 p-4 rounded border border-white/5 space-y-1">
                <div className="text-[10px] text-arkhe-muted uppercase">Zero-Point Power</div>
                <div className="text-xl font-bold text-amber-500 font-mono">{state.zeroPointPowerMw.toLocaleString()} MW</div>
             </div>
             <div className="bg-black/40 p-4 rounded border border-white/5 space-y-1">
                <div className="text-[10px] text-arkhe-muted uppercase">Fusion Efficiency</div>
                <div className="text-xl font-bold text-arkhe-cyan font-mono">{(state.fusionHeartEfficiency * 100).toFixed(2)}%</div>
             </div>
          </div>

          <div className="space-y-4">
             <div className="flex items-center gap-4 p-4 bg-white/5 rounded border border-white/10">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center border transition-colors ${state.eternalMode ? 'bg-amber-500/20 border-amber-500' : 'bg-black border-arkhe-border'}`}>
                   <Heart className={`w-5 h-5 ${state.eternalMode ? 'text-amber-500' : 'text-arkhe-muted'}`} />
                </div>
                <div>
                   <div className="text-xs font-mono font-bold text-arkhe-text uppercase">Eternal Fusion Heart</div>
                   <div className="text-[10px] font-mono text-arkhe-muted">
                      {state.eternalMode ? 'C Hearts are now self-sustaining via zero-point extraction.' : 'Awaiting Vacuum Coupling...'}
                   </div>
                </div>
             </div>

             <div className="flex items-center gap-4 p-4 bg-white/5 rounded border border-white/10">
                <div className="w-10 h-10 rounded-full flex items-center justify-center border bg-arkhe-cyan/20 border-arkhe-cyan">
                   <Activity className="w-5 h-5 text-arkhe-cyan" />
                </div>
                <div className="flex-1">
                   <div className="flex justify-between items-center mb-1">
                      <div className="text-xs font-mono font-bold text-arkhe-text uppercase">Vacuum Stability</div>
                      <div className="text-[10px] font-mono text-arkhe-cyan">{(state.vacuumStability * 100).toFixed(1)}%</div>
                   </div>
                   <div className="w-full bg-white/5 h-1.5 rounded-full overflow-hidden">
                      <motion.div
                         initial={{ width: 0 }}
                         animate={{ width: `${state.vacuumStability * 100}%` }}
                         className="h-full bg-arkhe-cyan shadow-[0_0_10px_rgba(0,255,255,0.5)]"
                      />
                   </div>
                </div>
             </div>
          </div>

          <button
            onClick={() => fetch('/api/energy/vacuum-harvest', { method: 'POST' })}
            className="w-full py-3 bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/50 rounded text-xs font-mono text-amber-500 transition-all uppercase tracking-widest font-bold shadow-[0_0_20px_rgba(245,158,11,0.2)]"
          >
            Initiate Zero-Point Extraction
          </button>
        </div>
      </motion.div>
    </div>
  );
}
