
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { X, Database, ShieldCheck, Zap, Activity, Clock } from 'lucide-react';
import { motion } from 'motion/react';
import React from 'react';

import type { QuantumMemoryState } from '../../server/types';

interface QuantumMemoryPanelProps {
  state?: QuantumMemoryState;
  onClose: () => void;
}

export default function QuantumMemoryPanel({ state, onClose }: QuantumMemoryPanelProps) {
  if (!state) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-[#0a0a0c] border border-amber-500/30 rounded-xl w-full max-w-2xl overflow-hidden shadow-[0_0_30px_rgba(245,158,11,0.1)] flex flex-col max-h-[90vh]"
      >
        <div className="p-4 border-b border-amber-500/20 flex justify-between items-center bg-amber-500/5">
          <div className="flex items-center gap-3">
            <Database className="w-5 h-5 text-amber-500" />
            <h2 className="font-mono text-sm uppercase tracking-widest text-amber-500 font-bold">2D Quantum Memory</h2>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto custom-scrollbar flex-1 space-y-6">
           <div className="grid grid-cols-2 gap-4">
              <div className="bg-black/40 p-4 rounded border border-white/5 space-y-1">
                 <div className="text-[10px] text-arkhe-muted uppercase">Stored Qubits</div>
                 <div className="text-xl font-bold text-amber-500 font-mono">{state.storedQubits}</div>
              </div>
              <div className="bg-black/40 p-4 rounded border border-white/5 space-y-1">
                 <div className="text-[10px] text-arkhe-muted uppercase">Memory Scaffold</div>
                 <div className="text-xl font-bold text-arkhe-text font-mono">{state.memoryMaterial}</div>
              </div>
           </div>

           <div className="bg-white/5 border border-white/10 p-4 rounded-lg space-y-4">
              <div className="flex items-center justify-between">
                 <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-arkhe-muted" />
                    <span className="text-xs font-mono text-arkhe-text uppercase">Coherence Time</span>
                 </div>
                 <span className="text-lg font-mono text-emerald-400 font-bold">{state.coherenceTimeSeconds.toFixed(2)} s</span>
              </div>

              <div className="space-y-1">
                 <div className="flex justify-between text-[10px] font-mono text-arkhe-muted uppercase">
                    <span>Retention Fidelity</span>
                    <span>{(state.retentionFidelity * 100).toFixed(2)}%</span>
                 </div>
                 <div className="w-full bg-white/5 h-1.5 rounded-full overflow-hidden">
                    <motion.div
                       initial={{ width: 0 }}
                       animate={{ width: `${state.retentionFidelity * 100}%` }}
                       className="h-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]"
                    />
                 </div>
              </div>
           </div>

           <div className="p-4 bg-amber-500/5 border border-amber-500/20 rounded space-y-3">
              <div className="flex items-center gap-2 text-amber-500">
                 <Activity className="w-4 h-4" />
                 <h3 className="text-xs font-mono font-bold uppercase">Active Registers</h3>
              </div>
              <div className="grid grid-cols-4 gap-2">
                 {Array.from({ length: 16 }).map((_, i) => (
                    <div key={i} className={`h-8 rounded border flex items-center justify-center text-[10px] font-mono ${i < state.activeRegisters ? 'bg-amber-500/20 border-amber-500 text-amber-400 animate-pulse' : 'bg-black border-white/5 text-arkhe-muted'}`}>
                       {i.toString(16).toUpperCase()}
                    </div>
                 ))}
              </div>
           </div>

           <button
              onClick={() => fetch('/api/quantum/memory/store', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ material: 'MoS2' }) })}
              className="w-full py-3 bg-amber-500/20 border border-amber-500/50 rounded text-xs font-mono text-amber-500 hover:bg-amber-500/30 transition-all uppercase tracking-widest font-bold"
           >
              Initialize 2D Storage Cycle
           </button>
        </div>

        <div className="p-4 border-t border-white/5 bg-black/40 flex items-center justify-between">
           <div className="text-[10px] font-mono text-arkhe-muted italic">
              "Valley and Spin symmetries protecting truth in two dimensions."
           </div>
           <ShieldCheck className="w-4 h-4 text-emerald-500" />
        </div>
      </motion.div>
    </div>
  );
}
