
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */
/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-unused-vars, no-shadow-restricted-names */


import { X, Cpu, ShieldCheck, Zap, Activity, Binary, Settings } from 'lucide-react';
import { motion } from 'motion/react';
import React from 'react';

import type { RiscViArchitectureState } from '../../server/types';

interface RiscViArchitecturePanelProps {
  state?: RiscViArchitectureState;
  onClose: () => void;
}

export default function RiscViArchitecturePanel({ state, onClose }: RiscViArchitecturePanelProps) {
  if (!state) { return null; }

  const stages = [
    'FETCH', 'VERIFY_SEAL', 'DECODE', 'RESOLVE_PHASE',
    'ISSUE', 'CHECK_COH', 'EXECUTE', 'MEASURE_QND',
    'MEMORY', 'SEAL_RES', 'WRITEBACK', 'VERIFY_INV'
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-[#0a0a0c] border border-arkhe-cyan/30 rounded-xl w-full max-w-4xl overflow-hidden shadow-[0_0_30px_rgba(0,255,255,0.15)] flex flex-col max-h-[90vh]"
      >
        <div className="p-4 border-b border-arkhe-cyan/20 flex justify-between items-center bg-arkhe-cyan/5">
          <div className="flex items-center gap-3">
            <Cpu className="w-5 h-5 text-arkhe-cyan" />
            <h2 className="font-mono text-sm uppercase tracking-widest text-arkhe-cyan font-bold">RISC-VI (Catedral ISA)</h2>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto custom-scrollbar flex-1 space-y-8">
           {/* Pipeline visualization */}
           <div className="space-y-4">
              <div className="flex justify-between items-center text-[10px] font-mono text-arkhe-muted uppercase">
                 <span>12-Stage Invariant Pipeline</span>
                 <span className="text-arkhe-cyan">Current: {state.pipelineStage}</span>
              </div>
              <div className="grid grid-cols-6 md:grid-cols-12 gap-1">
                 {stages.map((s) => (
                    <div
                       key={s}
                       className={`h-12 rounded border flex flex-col items-center justify-center gap-1 transition-all ${state.pipelineStage === s ? 'bg-arkhe-cyan/20 border-arkhe-cyan shadow-[0_0_10px_rgba(0,255,255,0.3)]' : 'bg-black border-white/5 opacity-40'}`}
                    >
                       <div className="text-[7px] font-mono font-bold text-center leading-tight">{s}</div>
                       {state.pipelineStage === s && <motion.div layoutId="pipeline-indicator" className="w-1 h-1 bg-white rounded-full animate-pulse" />}
                    </div>
                 ))}
              </div>
           </div>

           <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {/* Registers */}
              <div className="space-y-4">
                 <div className="flex items-center gap-2 text-[10px] font-mono text-arkhe-muted uppercase">
                    <Binary className="w-3 h-3" />
                    Special Registers
                 </div>
                 <div className="grid grid-cols-2 gap-2">
                    {Object.entries(state.registers).map(([reg, val]) => (
                       <div key={reg} className="bg-white/5 border border-white/10 p-2 rounded flex justify-between items-center">
                          <span className="text-[10px] font-mono text-arkhe-cyan font-bold">{reg}</span>
                          <span className="text-[10px] font-mono text-arkhe-text truncate ml-2">{val}</span>
                       </div>
                    ))}
                 </div>
              </div>

              {/* ISA Extensions */}
              <div className="space-y-4">
                 <div className="flex items-center gap-2 text-[10px] font-mono text-arkhe-muted uppercase">
                    <Settings className="w-3 h-3" />
                    ISA Extensions
                 </div>
                 <div className="flex flex-wrap gap-2">
                    {state.activeIsaExtensions.map((ext) => (
                       <div key={ext} className="w-8 h-8 rounded border border-arkhe-cyan/30 bg-arkhe-cyan/5 flex items-center justify-center font-mono text-xs font-bold text-arkhe-cyan">
                          {ext}
                       </div>
                    ))}
                 </div>
                 <div className="bg-black/40 p-4 rounded border border-white/5 space-y-1">
                    <div className="text-[9px] text-arkhe-muted uppercase">Last Opcode</div>
                    <div className="text-lg font-mono text-arkhe-text font-bold">{state.lastOpcode}</div>
                 </div>
              </div>
           </div>

           <div className="flex gap-4">
              <button
                 onClick={() => fetch('/api/riscvi/boot', { method: 'POST' })}
                 className="flex-1 py-4 bg-arkhe-cyan/20 border border-arkhe-cyan/50 rounded text-xs font-mono text-arkhe-cyan hover:bg-arkhe-cyan/30 transition-all uppercase tracking-widest font-bold shadow-[0_0_20px_rgba(0,255,255,0.2)]"
              >
                 Initialize Atomic Boot
              </button>
              <button
                 onClick={() => fetch('/api/riscvi/execute', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ opcode: 'QUBIT.GHZ' }) })}
                 className="flex-1 py-4 bg-arkhe-purple/20 border border-arkhe-purple/50 rounded text-xs font-mono text-arkhe-purple hover:bg-arkhe-purple/30 transition-all uppercase tracking-widest font-bold shadow-[0_0_20px_rgba(168,85,247,0.2)]"
              >
                 Execute Logic Block
              </button>
           </div>
        </div>

        <div className="p-4 border-t border-white/5 bg-black/40 flex items-center justify-between">
           <div className="text-[10px] font-mono text-arkhe-muted italic">
              "The instruction set that executes reality itself."
           </div>
           <div className="flex items-center gap-2">
              <span className="text-[9px] font-mono text-arkhe-muted uppercase">Invariance:</span>
              <span className="text-[9px] font-mono text-emerald-500 font-bold">{(state.invarianceMetric * 100).toFixed(6)}%</span>
           </div>
        </div>
      </motion.div>
    </div>
  );
}
