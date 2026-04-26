
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { X, BookOpen, ShieldCheck, Fingerprint, Zap, History } from 'lucide-react';
import { motion } from 'motion/react';
import React from 'react';

import type { QuantumCodexState } from '../../server/types';

interface QuantumCodexPanelProps {
  state?: QuantumCodexState;
  onClose: () => void;
}

export default function QuantumCodexPanel({ state, onClose }: QuantumCodexPanelProps) {
  if (!state) {return null;}

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-[#0a0a0c] border border-arkhe-purple/30 rounded-xl w-full max-w-4xl overflow-hidden shadow-[0_0_30px_rgba(168,85,247,0.15)] flex flex-col max-h-[90vh]"
      >
        <div className="p-4 border-b border-arkhe-purple/20 flex justify-between items-center bg-arkhe-purple/5">
          <div className="flex items-center gap-3">
            <BookOpen className="w-5 h-5 text-arkhe-purple" />
            <h2 className="font-mono text-sm uppercase tracking-widest text-arkhe-purple font-bold">Quantum Coherence Codex</h2>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto custom-scrollbar flex-1 space-y-6">
           <div className="flex justify-between items-center bg-black/40 p-4 rounded border border-white/5">
              <div className="space-y-1">
                 <div className="text-[10px] text-arkhe-muted uppercase tracking-tighter">Total Registrations</div>
                 <div className="text-2xl font-bold text-arkhe-purple font-mono">{state.totalRegistrations}</div>
              </div>
              <button
                 onClick={() => fetch('/api/quantum/codex/register', { method: 'POST' })}
                 className="px-4 py-2 bg-arkhe-purple/20 border border-arkhe-purple/50 rounded text-[10px] font-mono text-arkhe-purple hover:bg-arkhe-purple/30 transition-all uppercase font-bold"
              >
                 Register Testimony
              </button>
           </div>

           <div className="space-y-4">
              <div className="text-[10px] font-mono text-arkhe-muted uppercase flex items-center gap-2">
                 <History className="w-3 h-3" />
                 Invariance Testimonies
              </div>

              <div className="grid grid-cols-1 gap-2">
                 {state.entanglementInvariants.map((entry) => (
                    <div key={entry.id} className="bg-white/5 border border-white/10 p-3 rounded flex items-center gap-4 group hover:border-arkhe-purple/30 transition-all">
                       <div className="w-10 h-10 rounded bg-black flex items-center justify-center border border-white/5">
                          <Fingerprint className="w-5 h-5 text-arkhe-purple opacity-50 group-hover:opacity-100 transition-opacity" />
                       </div>
                       <div className="flex-1 min-w-0">
                          <div className="flex justify-between items-center">
                             <span className="text-xs font-mono font-bold text-arkhe-text">{entry.id}</span>
                             <span className="text-[8px] font-mono text-arkhe-muted">{entry.timestamp}</span>
                          </div>
                          <div className="text-[9px] font-mono text-arkhe-muted truncate">{entry.coherenceSeal}</div>
                          <div className="flex gap-4 mt-1">
                             <div className="text-[8px] font-mono text-arkhe-muted">ENTROPY: <span className="text-arkhe-purple">{entry.entropy.toFixed(3)} bits</span></div>
                             <div className="text-[8px] font-mono text-arkhe-muted">FIDELITY: <span className="text-emerald-500">{(entry.fidelity * 100).toFixed(2)}%</span></div>
                          </div>
                       </div>
                       <div className="text-right">
                          <div className="text-[9px] font-mono text-emerald-500 font-bold uppercase">{entry.topology}</div>
                          <div className="text-[8px] font-mono text-arkhe-muted uppercase">Verified</div>
                       </div>
                    </div>
                 ))}
                 {state.entanglementInvariants.length === 0 && (
                    <div className="h-40 flex flex-col items-center justify-center text-arkhe-muted space-y-2 border border-dashed border-white/10 rounded">
                       <Zap className="w-8 h-8 opacity-20" />
                       <span className="text-[10px] font-mono uppercase italic">Awaiting quantum testimony...</span>
                    </div>
                 )}
              </div>
           </div>
        </div>

        <div className="p-4 border-t border-white/5 bg-black/40 flex items-center justify-center gap-4">
           <ShieldCheck className="w-4 h-4 text-emerald-500" />
           <span className="text-[9px] font-mono text-arkhe-muted italic">"Preserving the topolgy of truth without collapsing the state of being."</span>
        </div>
      </motion.div>
    </div>
  );
}
