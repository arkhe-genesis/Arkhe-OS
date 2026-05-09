
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

/* eslint-disable @typescript-eslint/no-unused-vars */


import { X, Layers, Cpu, ShieldCheck, Zap, Activity } from 'lucide-react';
import { motion } from 'motion/react';
import React from 'react';

import type { QuantumNanoholeNetworkState } from '../../server/types';

interface QuantumNanoholeNetworkPanelProps {
  state?: QuantumNanoholeNetworkState;
  onClose: () => void;
}

export default function QuantumNanoholeNetworkPanel({ state, onClose }: QuantumNanoholeNetworkPanelProps) {
  if (!state) { return null; }

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
            <Layers className="w-5 h-5 text-arkhe-cyan" />
            <h2 className="font-mono text-sm uppercase tracking-widest text-arkhe-cyan font-bold">3D Quantum Nanohole Network</h2>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto custom-scrollbar flex-1">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
             {/* Left: Stats */}
             <div className="lg:col-span-1 space-y-6">
                <div className="bg-black/40 p-4 rounded border border-white/5 space-y-1">
                   <div className="text-[10px] text-arkhe-muted uppercase">Coherence Planes</div>
                   <div className="text-xl font-bold text-arkhe-cyan font-mono">{state.planesCount}</div>
                </div>
                <div className="bg-black/40 p-4 rounded border border-white/5 space-y-1">
                   <div className="text-[10px] text-arkhe-muted uppercase">Total Nanoholes</div>
                   <div className="text-xl font-bold text-arkhe-text font-mono">{state.totalNanoholes.toLocaleString()}</div>
                </div>
                <div className="bg-black/40 p-4 rounded border border-white/5 space-y-1">
                   <div className="text-[10px] text-arkhe-muted uppercase">Active Qubits</div>
                   <div className="text-xl font-bold text-emerald-500 font-mono">{state.activeQubits}</div>
                </div>

                <div className="p-4 bg-arkhe-cyan/5 border border-arkhe-cyan/20 rounded space-y-2">
                   <div className="flex items-center justify-between">
                      <span className="text-[10px] font-mono text-arkhe-cyan uppercase">Topological Index</span>
                      <span className="text-xs font-mono text-arkhe-cyan font-bold">{state.topologicalIndex.toFixed(4)}</span>
                   </div>
                   <div className="w-full bg-white/5 h-1.5 rounded-full overflow-hidden">
                      <motion.div
                         initial={{ width: 0 }}
                         animate={{ width: `${state.topologicalIndex * 100}%` }}
                         className="h-full bg-arkhe-cyan shadow-[0_0_10px_rgba(0,255,255,0.5)]"
                      />
                   </div>
                </div>
             </div>

             {/* Right: Visualization & GHZ State */}
             <div className="lg:col-span-2 space-y-6">
                <div className="bg-black/60 border border-arkhe-border rounded-lg p-8 flex flex-col items-center justify-center min-h-[300px] relative overflow-hidden">
                   {/* Stacked Planes Visualization */}
                   <div className="flex flex-col-reverse gap-1 items-center">
                      {Array.from({ length: 12 }).map((_, i) => (
                         <motion.div
                            key={i}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 0.1 + (i * 0.05), y: 0, scale: 0.8 + (i * 0.02) }}
                            className="w-48 h-12 border border-arkhe-cyan rounded-lg skew-x-[-20deg] bg-arkhe-cyan/5"
                         />
                      ))}
                   </div>

                   <div className="absolute inset-0 flex items-center justify-center">
                      <Activity className="w-24 h-24 text-arkhe-cyan/20 animate-pulse" />
                   </div>

                   <div className="absolute bottom-4 left-4 right-4 flex justify-between items-end">
                      <div>
                         <div className="text-[10px] font-mono text-arkhe-muted uppercase">Last GHZ State</div>
                         <div className="flex gap-1 mt-1">
                            {state.lastGhzState.map((bit, i) => (
                               <div key={i} className={`w-3 h-5 rounded-sm border ${bit === 1 ? 'bg-arkhe-cyan border-arkhe-cyan' : 'border-white/20'}`} />
                            ))}
                         </div>
                      </div>
                      <div className="text-right">
                         <div className="text-[10px] font-mono text-arkhe-muted uppercase">Protection</div>
                         <div className="text-[10px] font-mono text-emerald-500 font-bold uppercase">Surface Code d=7</div>
                      </div>
                   </div>
                </div>

                <button
                   onClick={() => fetch('/api/quantum/network/execute', { method: 'POST' })}
                   className="w-full py-4 bg-arkhe-cyan/20 hover:bg-arkhe-cyan/30 border border-arkhe-cyan/50 rounded text-xs font-mono text-arkhe-cyan transition-all uppercase tracking-widest font-bold shadow-[0_0_20px_rgba(0,255,255,0.2)] flex items-center justify-center gap-2"
                >
                   <Zap className="w-4 h-4" />
                   Execute Quantum Invariance Circuit
                </button>
             </div>
          </div>
        </div>

        <div className="p-4 border-t border-white/5 bg-black/40 flex items-center justify-center gap-6">
           <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-[9px] font-mono text-arkhe-muted uppercase tracking-widest">Global Coherence Lock Active</span>
           </div>
           <div className="flex items-center gap-2">
              <ShieldCheck className="w-3 h-3 text-arkhe-cyan" />
              <span className="text-[9px] font-mono text-arkhe-muted uppercase tracking-widest">Topological Protection Online</span>
           </div>
        </div>
      </motion.div>
    </div>
  );
}
