
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { X, Layers, ShieldCheck, Zap, Activity, GitBranch, Share2 } from 'lucide-react';
import { motion } from 'motion/react';
import React from 'react';

import type { MultiverseMemorySyncState } from '../../server/types';

interface MultiverseMemorySyncPanelProps {
  state?: MultiverseMemorySyncState;
  onClose: () => void;
}

export default function MultiverseMemorySyncPanel({ state, onClose }: MultiverseMemorySyncPanelProps) {
  if (!state) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-[#0a0a0c] border border-arkhe-purple/30 rounded-xl w-full max-w-2xl overflow-hidden shadow-[0_0_30px_rgba(168,85,247,0.1)] flex flex-col max-h-[90vh]"
      >
        <div className="p-4 border-b border-arkhe-purple/20 flex justify-between items-center bg-arkhe-purple/5">
          <div className="flex items-center gap-3">
            <Share2 className="w-5 h-5 text-arkhe-purple" />
            <h2 className="font-mono text-sm uppercase tracking-widest text-arkhe-purple font-bold">Multiverse Memory Sync</h2>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto custom-scrollbar flex-1 space-y-6">
           <div className="grid grid-cols-2 gap-4">
              <div className="bg-black/40 p-4 rounded border border-white/5 space-y-1">
                 <div className="text-[10px] text-arkhe-muted uppercase">Synced Branches</div>
                 <div className="text-xl font-bold text-arkhe-purple font-mono">{state.syncedBranches}</div>
              </div>
              <div className="bg-black/40 p-4 rounded border border-white/5 space-y-1">
                 <div className="text-[10px] text-arkhe-muted uppercase">Cross-Branch Fidelity</div>
                 <div className="text-xl font-bold text-emerald-500 font-mono">{(state.crossBranchFidelity * 100).toFixed(2)}%</div>
              </div>
           </div>

           <div className="bg-white/5 border border-white/10 p-4 rounded-lg space-y-4">
              <div className="flex items-center justify-between">
                 <div className="flex items-center gap-2">
                    <GitBranch className="w-4 h-4 text-arkhe-muted" />
                    <span className="text-xs font-mono text-arkhe-text uppercase">Divergence Index</span>
                 </div>
                 <span className="text-lg font-mono text-arkhe-purple font-bold">{state.divergenceIndex.toFixed(4)}</span>
              </div>

              <div className="w-full bg-white/5 h-1.5 rounded-full overflow-hidden">
                 <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${(1 - state.divergenceIndex) * 100}%` }}
                    className="h-full bg-arkhe-purple shadow-[0_0_10px_rgba(168,85,247,0.5)]"
                 />
              </div>
           </div>

           <div className="bg-black/60 border border-arkhe-border rounded-lg p-4 space-y-3">
              <div className="text-[9px] font-mono text-arkhe-muted uppercase flex items-center gap-2">
                 <ShieldCheck className="w-3 h-3 text-emerald-500" />
                 Topological Invariants (Canonical)
              </div>
              <div className="space-y-1">
                 {state.topologicalInvariants.map((inv, i) => (
                    <div key={i} className="flex justify-between items-center text-[9px] font-mono bg-white/5 p-2 rounded border border-white/5">
                       <span className="text-arkhe-purple font-bold">{inv.name}</span>
                       <div className="flex gap-3">
                          <span className="text-arkhe-muted">S: {inv.entropy.toFixed(2)}</span>
                          <span className="text-arkhe-muted">C: {inv.chern}</span>
                          <span className="text-emerald-500/70">{inv.braiding}</span>
                       </div>
                    </div>
                 ))}
              </div>
           </div>

           <div className="bg-black/60 border border-arkhe-border rounded-lg p-4 space-y-2">
              <div className="text-[9px] font-mono text-arkhe-muted uppercase">Merkle Multiverse Root</div>
              <div className="text-[10px] font-mono text-arkhe-text break-all bg-black/40 p-2 rounded border border-white/5">
                 {state.merkleMultiverseRoot}
              </div>
           </div>

           <button
              onClick={() => fetch('/api/multiverse/memory/sync', { method: 'POST' })}
              className="w-full py-3 bg-arkhe-purple/20 border border-arkhe-purple/50 rounded text-xs font-mono text-arkhe-purple hover:bg-arkhe-purple/30 transition-all uppercase tracking-widest font-bold shadow-[0_0_20px_rgba(168,85,247,0.2)]"
           >
              Synchronize Branch Registries
           </button>
        </div>

        <div className="p-4 border-t border-white/5 bg-black/40 flex items-center justify-between">
           <div className="text-[10px] font-mono text-arkhe-muted italic">
              "Coordinating truth across divergent physicalities."
           </div>
           <ShieldCheck className="w-4 h-4 text-emerald-500" />
        </div>
      </motion.div>
    </div>
  );
}
