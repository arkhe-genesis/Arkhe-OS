
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

/* eslint-disable @typescript-eslint/no-unused-vars */


import { X, Magnet, ShieldCheck, Zap, Activity, Brain, Infinity as InfinityIcon } from 'lucide-react';
import { motion } from 'motion/react';
import React from 'react';

import type { MagneticKnotState } from '../../server/types';

interface MagneticKnotPanelProps {
  state?: MagneticKnotState;
  onClose: () => void;
}

export default function MagneticKnotPanel({ state, onClose }: MagneticKnotPanelProps) {
  if (!state) { return null; }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-[#0a0a0c] border border-cyan-500/30 rounded-xl w-full max-w-2xl overflow-hidden shadow-[0_0_30px_rgba(6,182,212,0.1)] flex flex-col max-h-[90vh]"
      >
        <div className="p-4 border-b border-cyan-500/20 flex justify-between items-center bg-cyan-500/5">
          <div className="flex items-center gap-3">
            <Magnet className="w-5 h-5 text-cyan-400" />
            <h2 className="font-mono text-sm uppercase tracking-widest text-cyan-400 font-bold">3D Magnetic Knot Computing</h2>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto custom-scrollbar flex-1 space-y-6">
           <div className="grid grid-cols-2 gap-4">
              <div className="bg-black/40 p-4 rounded border border-white/5 space-y-1">
                 <div className="text-[10px] text-arkhe-muted uppercase">Magnetic Particles</div>
                 <div className="text-xl font-bold text-cyan-400 font-mono">{state.particleCount.toLocaleString()}</div>
              </div>
              <div className="bg-black/40 p-4 rounded border border-white/5 space-y-1">
                 <div className="text-[10px] text-arkhe-muted uppercase">Knot Complexity</div>
                 <div className="text-xl font-bold text-arkhe-purple font-mono">{(state.knotComplexity * 100).toFixed(1)}%</div>
              </div>
           </div>

           <div className="bg-black/60 border border-arkhe-border rounded-lg p-8 flex flex-col items-center justify-center min-h-[240px] relative overflow-hidden">
              {/* Knot Visualization */}
              <motion.div
                 animate={{ rotate: 360, scale: [1, 1.1, 1] }}
                 transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
                 className="w-32 h-32 border-4 border-cyan-500/30 rounded-full flex items-center justify-center"
              >
                 <InfinityIcon className="w-16 h-16 text-cyan-400 animate-pulse" />
              </motion.div>

              <div className="mt-6 text-center">
                 <div className={`text-xs font-mono font-bold uppercase ${state.neuronlikeComputingActive ? 'text-emerald-400' : 'text-arkhe-muted'}`}>
                    {state.neuronlikeComputingActive ? 'Neuronlike Computing: ACTIVE' : 'Computing Idle'}
                 </div>
                 <div className="text-[10px] font-mono text-arkhe-muted mt-1">
                    Resistance-free pathways: {state.resistanceFreePathways}
                 </div>
              </div>

              {/* Decorative particles */}
              {Array.from({ length: 12 }).map((_, i) => (
                 <motion.div
                    key={i}
                    animate={{
                       x: [Math.random() * 200 - 100, Math.random() * 200 - 100],
                       y: [Math.random() * 200 - 100, Math.random() * 200 - 100],
                       opacity: [0, 0.5, 0]
                    }}
                    transition={{ duration: 3 + Math.random() * 5, repeat: Infinity }}
                    className="absolute w-1 h-1 bg-cyan-400 rounded-full"
                 />
              ))}
           </div>

           <div className="space-y-2">
              <div className="text-[10px] font-mono text-arkhe-muted uppercase">Stored Geometries</div>
              <div className="flex flex-wrap gap-2">
                 {state.storedGeometries.map((g, i) => (
                    <span key={i} className="px-2 py-1 bg-white/5 border border-white/10 rounded text-[10px] font-mono text-arkhe-text">
                       {g}
                    </span>
                 ))}
              </div>
           </div>

           <button
              onClick={() => fetch('/api/magnetic/knot/compute', { method: 'POST' })}
              className="w-full py-3 bg-cyan-500/20 border border-cyan-500/50 rounded text-xs font-mono text-cyan-400 hover:bg-cyan-500/30 transition-all uppercase tracking-widest font-bold shadow-[0_0_20px_rgba(6,182,212,0.2)]"
           >
              Engage Neuronlike Processing
           </button>
        </div>

        <div className="p-4 border-t border-white/5 bg-black/40 flex items-center justify-between">
           <div className="text-[10px] font-mono text-arkhe-muted italic">
              "The days of electrical resistance are over."
           </div>
           <ShieldCheck className="w-4 h-4 text-emerald-500" />
        </div>
      </motion.div>
    </div>
  );
}
