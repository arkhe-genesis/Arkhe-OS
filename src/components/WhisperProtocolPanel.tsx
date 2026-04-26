
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { X, Mic, Zap, BarChart3, Database, Search } from 'lucide-react';
import { motion } from 'motion/react';
import React, { useState } from 'react';

import type { WhisperProtocolState } from '../../server/types';

interface WhisperProtocolPanelProps {
  state?: WhisperProtocolState;
  onClose: () => void;
}

export default function WhisperProtocolPanel({ state, onClose }: WhisperProtocolPanelProps) {
  const [selectedMaterial, setSelectedMaterial] = useState('Sapphire');

  if (!state) {return null;}

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-[#0a0a0c] border border-amber-500/30 rounded-xl w-full max-w-4xl overflow-hidden shadow-[0_0_30px_rgba(245,158,11,0.1)] flex flex-col max-h-[90vh]"
      >
        <div className="p-4 border-b border-amber-500/20 flex justify-between items-center bg-amber-500/5">
          <div className="flex items-center gap-3">
            <Mic className="w-5 h-5 text-amber-500" />
            <h2 className="font-mono text-sm uppercase tracking-widest text-amber-500 font-bold">Whisper Protocol Library</h2>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto custom-scrollbar flex-1">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
             {/* Material List */}
             <div className="lg:col-span-1 space-y-4">
                <div className="text-[10px] font-mono text-arkhe-muted uppercase mb-2 flex items-center gap-2">
                   <Database className="w-3 h-3" />
                   Material Scaffolds
                </div>
                <div className="space-y-1">
                   {state.calibrations.map((c) => (
                      <button
                         key={c.material}
                         onClick={() => setSelectedMaterial(c.material)}
                         className={`w-full p-3 flex flex-col items-start gap-1 rounded border transition-all ${selectedMaterial === c.material ? 'bg-amber-500/10 border-amber-500/50' : 'bg-white/5 border-white/10 hover:bg-white/10'}`}
                      >
                         <div className="flex justify-between w-full">
                            <span className="text-xs font-mono font-bold text-arkhe-text uppercase">{c.material}</span>
                            <span className="text-[8px] font-mono text-amber-500">{c.status}</span>
                         </div>
                         <div className="text-[9px] font-mono text-arkhe-muted">AR {c.aspectRatio.toFixed(0)}:1</div>
                      </button>
                   ))}
                   <button
                      onClick={() => fetch('/api/whisper/calibrate', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ material: 'Quartz' })
                      })}
                      className="w-full p-3 flex items-center justify-center gap-2 rounded border border-dashed border-white/20 text-[10px] font-mono text-arkhe-muted hover:text-white hover:border-white/40 transition-all"
                   >
                      <Zap className="w-3 h-3" />
                      NEW CALIBRATION
                   </button>
                </div>
             </div>

             {/* Detail View */}
             <div className="lg:col-span-2 space-y-6">
                {state.calibrations.find(c => c.material === selectedMaterial) ? (
                   <>
                      <div className="bg-black/40 p-6 rounded-lg border border-white/5 space-y-4">
                         <div className="flex items-center justify-between border-b border-white/10 pb-4">
                            <h3 className="text-xl font-bold text-amber-500 font-mono uppercase">{selectedMaterial} Calibration</h3>
                            <BarChart3 className="w-5 h-5 text-arkhe-muted" />
                         </div>

                         <div className="grid grid-cols-2 gap-6">
                            <div className="space-y-1">
                               <div className="text-[10px] text-arkhe-muted uppercase">Pulse Duration</div>
                               <div className="text-lg font-mono text-arkhe-text">{state.calibrations.find(c => c.material === selectedMaterial)?.pulseDurationFs.toFixed(1)} fs</div>
                            </div>
                            <div className="space-y-1">
                               <div className="text-[10px] text-arkhe-muted uppercase">Chirp Rate</div>
                               <div className="text-lg font-mono text-arkhe-text">{state.calibrations.find(c => c.material === selectedMaterial)?.chirpRateFs2.toFixed(1)} fs²</div>
                            </div>
                            <div className="space-y-1">
                               <div className="text-[10px] text-arkhe-muted uppercase">Aspect Ratio</div>
                               <div className="text-lg font-mono text-emerald-400">{state.calibrations.find(c => c.material === selectedMaterial)?.aspectRatio.toFixed(0)}:1</div>
                            </div>
                            <div className="space-y-1">
                               <div className="text-[10px] text-arkhe-muted uppercase">Wall Roughness</div>
                               <div className="text-lg font-mono text-cyan-400">{state.calibrations.find(c => c.material === selectedMaterial)?.roughnessNm.toFixed(3)} nm</div>
                            </div>
                         </div>
                      </div>

                      <div className="bg-amber-500/5 p-4 rounded border border-amber-500/20">
                         <div className="text-[10px] font-mono text-amber-500 uppercase mb-2">Geometric Persuasion Logic</div>
                         <div className="text-[9px] font-mono text-arkhe-muted leading-relaxed italic">
                            "The pulse profile is optimized to resound with {selectedMaterial}'s intrinsic phonon dispersion modes.
                            By matching the spectral phase to the lattice anisotropy, we induce spontaneous geometric reorganization."
                         </div>
                      </div>
                   </>
                ) : (
                   <div className="h-full flex flex-col items-center justify-center text-arkhe-muted space-y-4">
                      <Search className="w-12 h-12 opacity-20" />
                      <div className="text-xs font-mono uppercase">Select a material to view whisper profile</div>
                   </div>
                )}
             </div>
          </div>
        </div>

        <div className="p-4 border-t border-white/5 bg-black/40 flex justify-between items-center shrink-0">
           <div className="flex gap-4">
              <div className="text-[10px] font-mono">
                 <span className="text-arkhe-muted uppercase mr-2">Total Whispers:</span>
                 <span className="text-arkhe-text">{state.totalWhispers.toLocaleString()}</span>
              </div>
              <div className="text-[10px] font-mono">
                 <span className="text-arkhe-muted uppercase mr-2">Success Rate:</span>
                 <span className="text-emerald-500">{(state.successRate * 100).toFixed(2)}%</span>
              </div>
           </div>
           <div className="text-[10px] font-mono text-arkhe-muted italic">
              Awaiting resonance...
           </div>
        </div>
      </motion.div>
    </div>
  );
}
