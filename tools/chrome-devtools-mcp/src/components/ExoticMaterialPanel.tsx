
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { X, Sparkles, Zap, ShieldCheck, Plus, Thermometer } from 'lucide-react';
import { motion } from 'motion/react';
import React from 'react';

import type { ExoticMaterialState } from '../../server/types';

interface ExoticMaterialPanelProps {
  state?: ExoticMaterialState;
  onClose: () => void;
}

export default function ExoticMaterialPanel({ state, onClose }: ExoticMaterialPanelProps) {
  if (!state) { return null; }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-[#0a0a0c] border border-amber-500/30 rounded-xl w-full max-w-3xl overflow-hidden shadow-[0_0_30px_rgba(245,158,11,0.15)] flex flex-col max-h-[90vh]"
      >
        <div className="p-4 border-b border-amber-500/20 flex justify-between items-center bg-amber-500/5">
          <div className="flex items-center gap-3">
            <Sparkles className="w-5 h-5 text-amber-500" />
            <h2 className="font-mono text-sm uppercase tracking-widest text-amber-500 font-bold">Exotic Material Scaffolds</h2>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto custom-scrollbar flex-1">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
             {state.scaffolds.map((s) => (
                <div key={s.name} className="bg-white/5 border border-white/10 p-4 rounded-lg space-y-3 group hover:border-amber-500/30 transition-all">
                   <div className="flex justify-between items-start">
                      <div>
                         <h3 className="text-sm font-mono font-bold text-arkhe-text uppercase">{s.name}</h3>
                         <div className="text-[8px] font-mono text-amber-500/70 font-bold uppercase">{s.type}</div>
                      </div>
                      <div className="px-2 py-0.5 bg-emerald-500/10 border border-emerald-500/30 rounded text-[8px] font-mono text-emerald-400">
                         PERSUADED
                      </div>
                   </div>

                   <div className="flex justify-between items-center bg-black/40 p-2 rounded">
                      <div className="flex items-center gap-2">
                         <Thermometer className="w-3 h-3 text-arkhe-muted" />
                         <span className="text-[9px] font-mono text-arkhe-muted uppercase">Resonance</span>
                      </div>
                      <div className="text-xs font-mono text-arkhe-text">{s.resonanceTHz} THz</div>
                   </div>

                   {s.excitonBindingMeV && (
                      <div className="flex justify-between items-center px-1">
                         <span className="text-[8px] font-mono text-arkhe-muted uppercase">Exciton Binding</span>
                         <span className="text-[8px] font-mono text-amber-400">{s.excitonBindingMeV} meV</span>
                      </div>
                   )}

                   <div className="space-y-1">
                      <div className="flex justify-between text-[8px] font-mono text-arkhe-muted uppercase">
                         <span>Persuasion Level</span>
                         <span>{(s.persuasionLevel * 100).toFixed(0)}%</span>
                      </div>
                      <div className="w-full bg-white/5 h-1 rounded-full overflow-hidden">
                         <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${s.persuasionLevel * 100}%` }}
                            className="h-full bg-amber-500 shadow-[0_0_10px_rgba(245,158,11,0.5)]"
                         />
                      </div>
                   </div>
                </div>
             ))}

             <button
                onClick={() => fetch('/api/whisper/library/exotic', {
                   method: 'POST',
                   headers: { 'Content-Type': 'application/json' },
                   body: JSON.stringify({ name: 'WS2 Monolayer', type: 'TMD', resonance: 10.5, exciton: 60 })
                })}
                className="flex flex-col items-center justify-center p-4 rounded border border-dashed border-white/20 hover:border-amber-500/50 hover:bg-amber-500/5 transition-all group"
             >
                <Plus className="w-6 h-6 text-arkhe-muted group-hover:text-amber-500 mb-2" />
                <span className="text-[10px] font-mono text-arkhe-muted group-hover:text-arkhe-text uppercase tracking-widest">Add Exotic Scaffold</span>
             </button>
          </div>
        </div>

        <div className="p-4 border-t border-white/5 bg-black/40 flex items-center justify-between">
           <div className="flex items-center gap-2">
              <Zap className="w-3 h-3 text-amber-500" />
              <span className="text-[9px] font-mono text-arkhe-muted uppercase tracking-widest">Universal Resonance Database Active</span>
           </div>
           <ShieldCheck className="w-4 h-4 text-arkhe-cyan opacity-50" />
        </div>
      </motion.div>
    </div>
  );
}
