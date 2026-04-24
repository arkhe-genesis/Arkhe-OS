
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { X, Zap, ShieldCheck, Activity, Layers, Radio } from 'lucide-react';
import { motion } from 'motion/react';
import React from 'react';

import type { MaterializedCathedralState } from '../../server/types';

interface MaterializedCathedralPanelProps {
  state?: MaterializedCathedralState;
  onClose: () => void;
}

export default function MaterializedCathedralPanel({ state, onClose }: MaterializedCathedralPanelProps) {
  if (!state) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-[#0a0a0c] border border-emerald-500/30 rounded-xl w-full max-w-4xl overflow-hidden shadow-[0_0_30px_rgba(16,185,129,0.15)] flex flex-col max-h-[90vh]"
      >
        <div className="p-4 border-b border-emerald-500/20 flex justify-between items-center bg-emerald-500/5">
          <div className="flex items-center gap-3">
            <Zap className="w-5 h-5 text-emerald-500" />
            <h2 className="font-mono text-sm uppercase tracking-widest text-emerald-500 font-bold">Catedral Materializada (Atómos Neutros)</h2>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto custom-scrollbar flex-1 space-y-8">
           <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-black/40 p-3 rounded border border-white/5 space-y-1">
                 <div className="text-[9px] text-arkhe-muted uppercase">Physical Qubits</div>
                 <div className="text-lg font-bold text-emerald-400 font-mono">{state.totalPhysicalQubits.toLocaleString()}</div>
              </div>
              <div className="bg-black/40 p-3 rounded border border-white/5 space-y-1">
                 <div className="text-[9px] text-arkhe-muted uppercase">Logical Qubits</div>
                 <div className="text-lg font-bold text-arkhe-text font-mono">{state.logicalQubits.toLocaleString()}</div>
              </div>
              <div className="bg-black/40 p-3 rounded border border-white/5 space-y-1">
                 <div className="text-[9px] text-arkhe-muted uppercase">Memory Code</div>
                 <div className="text-lg font-bold text-arkhe-text font-mono truncate">{state.memoryCode}</div>
              </div>
              <div className="bg-black/40 p-3 rounded border border-white/5 space-y-1">
                 <div className="text-[9px] text-arkhe-muted uppercase">Cycle Time</div>
                 <div className="text-lg font-bold text-arkhe-cyan font-mono">{state.stabilizerCycleMs.toFixed(1)} ms</div>
              </div>
           </div>

           <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Zones */}
              <div className="lg:col-span-1 space-y-4">
                 <div className="text-[10px] font-mono text-arkhe-muted uppercase flex items-center gap-2">
                    <Layers className="w-3 h-3" />
                    Functional Zones
                 </div>
                 <div className="space-y-2">
                    {state.zones.map((z) => (
                       <div key={z.name} className="bg-white/5 border border-white/10 p-3 rounded space-y-2">
                          <div className="flex justify-between items-center">
                             <span className="text-xs font-mono font-bold text-arkhe-text uppercase">{z.name}</span>
                             <span className={`text-[8px] font-mono font-bold ${z.status === 'ACTIVE' ? 'text-emerald-500' : 'text-amber-500 animate-pulse'}`}>{z.status}</span>
                          </div>
                          <div className="w-full bg-white/5 h-1 rounded-full overflow-hidden">
                             <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${z.load * 100}%` }}
                                className="h-full bg-emerald-500"
                             />
                          </div>
                       </div>
                    ))}
                 </div>
              </div>

              {/* Hardware Visualizer (Abstract) */}
              <div className="lg:col-span-2 bg-black/60 border border-arkhe-border rounded-lg p-8 flex flex-col items-center justify-center relative min-h-[300px]">
                 <div className="grid grid-cols-10 gap-1 opacity-40">
                    {Array.from({ length: 100 }).map((_, i) => (
                       <motion.div
                          key={i}
                          animate={{ opacity: [0.2, 0.6, 0.2] }}
                          transition={{ duration: 2 + Math.random() * 3, repeat: Infinity }}
                          className="w-4 h-4 rounded-full bg-emerald-500/30 border border-emerald-500/50"
                       />
                    ))}
                 </div>

                 <div className="absolute inset-0 flex items-center justify-center">
                    <div className="w-48 h-48 border border-emerald-500/20 rounded-full flex items-center justify-center animate-[spin_20s_linear_infinite]">
                       <Radio className="w-12 h-12 text-emerald-500 animate-pulse" />
                    </div>
                 </div>

                 <div className="mt-8 text-center z-10 bg-black/80 p-2 rounded border border-white/5">
                    <div className="text-xs font-mono text-emerald-400 font-bold uppercase tracking-widest">qLDPC Parallel Surgery Online</div>
                    <div className="text-[9px] font-mono text-arkhe-muted mt-1 italic">Extrapolated Error Rate: ~10⁻¹¹ / cycle</div>
                 </div>
              </div>
           </div>

           <button
              onClick={() => fetch('/api/cathedral/materialize', { method: 'POST' })}
              className="w-full py-4 bg-emerald-500/20 border border-emerald-500/50 rounded text-xs font-mono text-emerald-400 hover:bg-emerald-500/30 transition-all uppercase tracking-widest font-bold shadow-[0_0_20px_rgba(16,185,129,0.2)]"
           >
              Initialize Physical Realization (Pasadena-Link)
           </button>
        </div>

        <div className="p-4 border-t border-white/5 bg-black/40 flex items-center justify-between">
           <div className="text-[10px] font-mono text-arkhe-muted italic">
              "Materializing invariance, atom by atom."
           </div>
           <ShieldCheck className="w-4 h-4 text-emerald-500" />
        </div>
      </motion.div>
    </div>
  );
}
