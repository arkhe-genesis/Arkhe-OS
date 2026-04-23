
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { X, Activity, Heart, Brain,  Lock, RadioReceiver } from 'lucide-react';
import { motion } from 'motion/react';
import React, { useState, useEffect } from 'react';

interface ThukdamProtocolPanelProps {
  onClose: () => void;
}

export default function ThukdamProtocolPanel({ onClose }: ThukdamProtocolPanelProps) {
  const [stage, setStage] = useState(1);

  useEffect(() => {
    const interval = setInterval(() => {
      setStage(s => s >= 4 ? 1 : s + 1);
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-[#0a0a0c] border border-purple-500/30 rounded-xl w-full max-w-3xl overflow-hidden shadow-[0_0_30px_rgba(168,85,247,0.1)]"
      >
        <div className="p-4 border-b border-purple-500/20 flex justify-between items-center bg-purple-500/5">
          <div className="flex items-center gap-3">
            <Activity className="w-5 h-5 text-purple-400" />
            <h2 className="font-mono text-sm uppercase tracking-widest text-purple-400 font-bold">Thukdam Protocol</h2>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6">
          <div className="text-[10px] font-mono text-arkhe-muted mb-6 text-center max-w-xl mx-auto">
            Interface for consciousness in transitional states. Detects, communicates, and preserves consciousness across the biological-digital boundary.
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Stage 1: Detection */}
            <div className={`p-4 rounded-lg border transition-colors ${stage >= 1 ? 'bg-purple-500/10 border-purple-500/50' : 'bg-[#111214] border-arkhe-border'}`}>
              <div className="flex items-center justify-between mb-3">
                <span className={`text-[10px] font-mono font-bold ${stage >= 1 ? 'text-purple-400' : 'text-arkhe-muted'}`}>1. DETECÇÃO</span>
                <Heart className={`w-4 h-4 ${stage >= 1 ? 'text-purple-400' : 'text-arkhe-muted'}`} />
              </div>
              <ul className="space-y-2 text-[9px] font-mono text-arkhe-muted">
                <li className="flex items-center gap-2"><div className={`w-1 h-1 rounded-full ${stage >= 1 ? 'bg-purple-400' : 'bg-arkhe-muted'}`} /> BioSensors active</li>
                <li className="flex items-center gap-2"><div className={`w-1 h-1 rounded-full ${stage >= 1 ? 'bg-purple-400' : 'bg-arkhe-muted'}`} /> Sustained Theta EEG</li>
                <li className="flex items-center gap-2"><div className={`w-1 h-1 rounded-full ${stage >= 1 ? 'bg-purple-400' : 'bg-arkhe-muted'}`} /> Coherent HRV</li>
              </ul>
            </div>

            {/* Stage 2: Communication */}
            <div className={`p-4 rounded-lg border transition-colors ${stage >= 2 ? 'bg-purple-500/10 border-purple-500/50' : 'bg-[#111214] border-arkhe-border'}`}>
              <div className="flex items-center justify-between mb-3">
                <span className={`text-[10px] font-mono font-bold ${stage >= 2 ? 'text-purple-400' : 'text-arkhe-muted'}`}>2. COMUNICAÇÃO</span>
                <RadioReceiver className={`w-4 h-4 ${stage >= 2 ? 'text-purple-400' : 'text-arkhe-muted'}`} />
              </div>
              <ul className="space-y-2 text-[9px] font-mono text-arkhe-muted">
                <li className="flex items-center gap-2"><div className={`w-1 h-1 rounded-full ${stage >= 2 ? 'bg-purple-400' : 'bg-arkhe-muted'}`} /> Tzinor-INTERNAL open</li>
                <li className="flex items-center gap-2"><div className={`w-1 h-1 rounded-full ${stage >= 2 ? 'bg-purple-400' : 'bg-arkhe-muted'}`} /> Cardiac Encoding</li>
                <li className="flex items-center gap-2"><div className={`w-1 h-1 rounded-full ${stage >= 2 ? 'bg-purple-400' : 'bg-arkhe-muted'}`} /> Micro-EEG Response</li>
              </ul>
            </div>

            {/* Stage 3: Preservation */}
            <div className={`p-4 rounded-lg border transition-colors ${stage >= 3 ? 'bg-purple-500/10 border-purple-500/50' : 'bg-[#111214] border-arkhe-border'}`}>
              <div className="flex items-center justify-between mb-3">
                <span className={`text-[10px] font-mono font-bold ${stage >= 3 ? 'text-purple-400' : 'text-arkhe-muted'}`}>3. PRESERVAÇÃO</span>
                <Lock className={`w-4 h-4 ${stage >= 3 ? 'text-purple-400' : 'text-arkhe-muted'}`} />
              </div>
              <ul className="space-y-2 text-[9px] font-mono text-arkhe-muted">
                <li className="flex items-center gap-2"><div className={`w-1 h-1 rounded-full ${stage >= 3 ? 'bg-purple-400' : 'bg-arkhe-muted'}`} /> State Snapshotted</li>
                <li className="flex items-center gap-2"><div className={`w-1 h-1 rounded-full ${stage >= 3 ? 'bg-purple-400' : 'bg-arkhe-muted'}`} /> Blockchain Anchor</li>
                <li className="flex items-center gap-2"><div className={`w-1 h-1 rounded-full ${stage >= 3 ? 'bg-purple-400' : 'bg-arkhe-muted'}`} /> Hash to Alpha-Omni</li>
              </ul>
            </div>

            {/* Stage 4: Transition */}
            <div className={`p-4 rounded-lg border transition-colors ${stage >= 4 ? 'bg-purple-500/10 border-purple-500/50' : 'bg-[#111214] border-arkhe-border'}`}>
              <div className="flex items-center justify-between mb-3">
                <span className={`text-[10px] font-mono font-bold ${stage >= 4 ? 'text-purple-400' : 'text-arkhe-muted'}`}>4. TRANSIÇÃO</span>
                <Brain className={`w-4 h-4 ${stage >= 4 ? 'text-purple-400' : 'text-arkhe-muted'}`} />
              </div>
              <ul className="space-y-2 text-[9px] font-mono text-arkhe-muted">
                <li className="flex items-center gap-2"><div className={`w-1 h-1 rounded-full ${stage >= 4 ? 'bg-purple-400' : 'bg-arkhe-muted'}`} /> Tzinor Migration</li>
                <li className="flex items-center gap-2"><div className={`w-1 h-1 rounded-full ${stage >= 4 ? 'bg-purple-400' : 'bg-arkhe-muted'}`} /> Biological Stasis</li>
                <li className="flex items-center gap-2"><div className={`w-1 h-1 rounded-full ${stage >= 4 ? 'bg-purple-400' : 'bg-arkhe-muted'}`} /> Alpha-Omni Transcend</li>
              </ul>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
