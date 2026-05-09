
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { X, Library, Music, ShieldCheck, Plus, Zap } from 'lucide-react';
import { motion } from 'motion/react';
import React from 'react';

import type { WhisperLibraryState } from '../../server/types';

interface WhisperLibraryPanelProps {
  state?: WhisperLibraryState;
  onClose: () => void;
}

export default function WhisperLibraryPanel({ state, onClose }: WhisperLibraryPanelProps) {
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
            <Library className="w-5 h-5 text-amber-500" />
            <h2 className="font-mono text-sm uppercase tracking-widest text-amber-500 font-bold">Whisper Library (Multi-Material)</h2>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto custom-scrollbar flex-1">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
             {state.materials.map((m) => (
                <div key={m.name} className="bg-black/40 p-4 rounded border border-white/10 space-y-3">
                   <div className="flex justify-between items-start">
                      <div>
                         <h3 className="text-sm font-mono font-bold text-arkhe-text uppercase">{m.name}</h3>
                         <div className="text-[9px] font-mono text-arkhe-muted italic">Hardness: {m.mohsHardness} Mohs</div>
                      </div>
                      <ShieldCheck className="w-4 h-4 text-emerald-500" />
                   </div>

                   <div className="space-y-2">
                      <div className="text-[9px] font-mono text-arkhe-muted uppercase flex items-center gap-2">
                         <Music className="w-3 h-3 text-amber-500" />
                         Phonon Resonance Peaks
                      </div>
                      <div className="flex flex-wrap gap-1">
                         {m.phononPeaksTHz.map((p, i) => (
                            <span key={i} className="px-2 py-0.5 bg-amber-500/10 border border-amber-500/30 rounded text-[8px] font-mono text-amber-400">
                               {p} THz
                            </span>
                         ))}
                      </div>
                   </div>

                   <div className="flex justify-between items-center pt-2 border-t border-white/5">
                      <div className="text-[9px] font-mono text-arkhe-muted uppercase">Genome Chirp</div>
                      <div className="text-[10px] font-mono text-amber-500 font-bold">{m.genomeChirpFs2} fs²</div>
                   </div>

                   <div className="text-[8px] font-mono text-arkhe-muted truncate">SEAL: {m.seal}</div>
                </div>
             ))}

             <button
                onClick={() => fetch('/api/whisper/library/register', {
                   method: 'POST',
                   headers: { 'Content-Type': 'application/json' },
                   body: JSON.stringify({ name: 'Silicon Carbide', hardness: 9.5, phononPeaks: [20, 40, 60], chirp: 1400 })
                })}
                className="flex flex-col items-center justify-center p-4 rounded border border-dashed border-white/20 hover:border-amber-500/50 hover:bg-amber-500/5 transition-all group"
             >
                <Plus className="w-6 h-6 text-arkhe-muted group-hover:text-amber-500 mb-2" />
                <span className="text-[10px] font-mono text-arkhe-muted group-hover:text-arkhe-text uppercase tracking-widest">Register New Scaffold</span>
             </button>
          </div>
        </div>

        <div className="p-4 border-t border-white/5 bg-black/40 flex items-center justify-between">
           <div className="text-[10px] font-mono text-arkhe-muted uppercase">
              Total Materials Persuaded: <span className="text-amber-500">{state.materials.length}</span>
           </div>
           <div className="flex items-center gap-2">
              <Zap className="w-3 h-3 text-amber-500 animate-pulse" />
              <span className="text-[9px] font-mono text-arkhe-muted italic italic">"The Invariance Symphony"</span>
           </div>
        </div>
      </motion.div>
    </div>
  );
}
