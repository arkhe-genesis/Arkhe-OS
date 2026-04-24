
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { X, Layers, Cpu, ShieldCheck, Zap, Activity, Share2 } from 'lucide-react';
import { motion } from 'motion/react';
import React from 'react';

import type { HybridNetworkState } from '../../server/types';

interface HybridNetworkPanelProps {
  state?: HybridNetworkState;
  onClose: () => void;
}

export default function HybridNetworkPanel({ state, onClose }: HybridNetworkPanelProps) {
  if (!state) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-[#0a0a0c] border border-arkhe-cyan/30 rounded-xl w-full max-w-4xl overflow-hidden shadow-[0_0_30px_rgba(0,255,255,0.1)] flex flex-col max-h-[90vh]"
      >
        <div className="p-4 border-b border-arkhe-cyan/20 flex justify-between items-center bg-arkhe-cyan/5">
          <div className="flex items-center gap-3">
            <Share2 className="w-5 h-5 text-arkhe-cyan" />
            <h2 className="font-mono text-sm uppercase tracking-widest text-arkhe-cyan font-bold">Hybrid 3D-2D Network</h2>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto custom-scrollbar flex-1 space-y-8">
           <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-black/40 p-3 rounded border border-white/5 space-y-1">
                 <div className="text-[9px] text-arkhe-muted uppercase">Integrated Nodes</div>
                 <div className="text-lg font-bold text-arkhe-cyan font-mono">{state.integratedNodes}</div>
              </div>
              <div className="bg-black/40 p-3 rounded border border-white/5 space-y-1">
                 <div className="text-[9px] text-arkhe-muted uppercase">Graphene Circuits</div>
                 <div className="text-lg font-bold text-arkhe-text font-mono">{state.grapheneCircuits}</div>
              </div>
              <div className="bg-black/40 p-3 rounded border border-white/5 space-y-1">
                 <div className="text-[9px] text-arkhe-muted uppercase">Sapphire Nanoholes</div>
                 <div className="text-lg font-bold text-arkhe-text font-mono">{state.sapphireNanoholes.toLocaleString()}</div>
              </div>
              <div className="bg-black/40 p-3 rounded border border-white/5 space-y-1">
                 <div className="text-[9px] text-arkhe-muted uppercase">Hybrid Coherence</div>
                 <div className="text-lg font-bold text-emerald-500 font-mono">{state.hybridCoherenceTimeMs} ms</div>
              </div>
           </div>

           <div className="flex flex-col items-center justify-center p-12 bg-black/60 border border-arkhe-border rounded-lg relative overflow-hidden min-h-[300px]">
              {/* Hybrid Visualization */}
              <div className="relative w-64 h-64">
                 {/* Graphene Layer (2D) */}
                 <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                    className="absolute inset-0 border-2 border-dashed border-amber-500/30 rounded-full flex items-center justify-center"
                 >
                    <div className="w-full h-px bg-amber-500/20 absolute rotate-0" />
                    <div className="w-full h-px bg-amber-500/20 absolute rotate-60" />
                    <div className="w-full h-px bg-amber-500/20 absolute rotate-120" />
                 </motion.div>

                 {/* Sapphire Bulk (3D) */}
                 <div className="absolute inset-12 border border-arkhe-cyan/50 rounded-lg flex flex-col gap-2 p-4 bg-arkhe-cyan/5">
                    {Array.from({ length: 5 }).map((_, i) => (
                       <div key={i} className="h-2 w-full bg-arkhe-cyan/20 rounded-sm" />
                    ))}
                 </div>

                 {/* Coupling Points */}
                 <div className="absolute inset-0 flex items-center justify-center">
                    <Activity className="w-16 h-16 text-emerald-500/40 animate-pulse" />
                 </div>
              </div>

              <div className="mt-8 text-center">
                 <div className="text-xs font-mono text-arkhe-text uppercase font-bold">Evanescent Coupling Interface</div>
                 <div className="text-[10px] font-mono text-arkhe-muted">Coupling Efficiency: {(state.couplingEfficiency * 100).toFixed(2)}%</div>
              </div>
           </div>

           <button
              onClick={() => fetch('/api/hybrid/integrate', { method: 'POST' })}
              className="w-full py-4 bg-arkhe-cyan/20 border border-arkhe-cyan/50 rounded text-xs font-mono text-arkhe-cyan hover:bg-arkhe-cyan/30 transition-all uppercase tracking-widest font-bold shadow-[0_0_20px_rgba(0,255,255,0.2)]"
           >
              Integrate 3D Sapphire with 2D Graphene
           </button>
        </div>

        <div className="p-4 border-t border-white/5 bg-black/40 flex items-center justify-between">
           <div className="text-[10px] font-mono text-arkhe-muted italic">
              "Fusing volume and surface into a single coherent manifold."
           </div>
           <ShieldCheck className="w-4 h-4 text-emerald-500" />
        </div>
      </motion.div>
    </div>
  );
}
