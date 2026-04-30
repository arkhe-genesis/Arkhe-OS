
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */
/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-unused-vars, no-shadow-restricted-names */


import { X, Sparkles, Binary, ShieldCheck, Zap } from 'lucide-react';
import { motion } from 'motion/react';
import React, { useState } from 'react';

import type { MetaCreationState } from '../../server/types';

interface MetaCreationPanelProps {
  state?: MetaCreationState;
  onClose: () => void;
}

export default function MetaCreationPanel({ state, onClose }: MetaCreationPanelProps) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);

  if (!state) {return null;}

  const handleGenerate = async () => {
    setIsGenerating(true);
    setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] CONCEPT: Initializing Logical Seed...`]);

    setTimeout(() => {
      setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] MAPPING: Translating Invariants to Physics...`]);
      setTimeout(() => {
        setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] INSTANTIATION: Decoupling Causal Horizon...`]);
        setTimeout(async () => {
          await fetch('/api/metacreation/generate', { method: 'POST' });
          setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] GENESIS: Reality Established. Seal registered.`]);
          setIsGenerating(false);
        }, 1500);
      }, 1500);
    }, 1500);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-[#0a0a0c] border border-arkhe-purple/30 rounded-xl w-full max-w-2xl overflow-hidden shadow-[0_0_30px_rgba(168,85,247,0.1)] flex flex-col"
      >
        <div className="p-4 border-b border-arkhe-purple/20 flex justify-between items-center bg-arkhe-purple/5">
          <div className="flex items-center gap-3">
            <Sparkles className="w-5 h-5 text-arkhe-purple" />
            <h2 className="font-mono text-sm uppercase tracking-widest text-arkhe-purple font-bold">Meta-Creation Engine</h2>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          <div className="grid grid-cols-2 gap-4">
             <div className="bg-black/40 p-4 rounded border border-white/5 space-y-1">
                <div className="text-[10px] text-arkhe-muted uppercase">Realities Created</div>
                <div className="text-xl font-bold text-arkhe-purple font-mono">{state.realitiesCreated}</div>
             </div>
             <div className="bg-black/40 p-4 rounded border border-white/5 space-y-1">
                <div className="text-[10px] text-arkhe-muted uppercase">Logical Consistency</div>
                <div className="text-xl font-bold text-emerald-500 font-mono">{(state.logicalConsistency * 100).toFixed(4)}%</div>
             </div>
          </div>

          <div className="bg-black/60 border border-arkhe-border rounded-lg p-3 h-40 flex flex-col">
             <div className="flex items-center gap-2 mb-2 text-arkhe-muted">
                <Binary className="w-3 h-3" />
                <span className="text-[10px] font-mono uppercase">Genesis Logs</span>
             </div>
             <div className="flex-1 overflow-y-auto custom-scrollbar space-y-1">
                {logs.map((log, i) => (
                   <div key={i} className="text-[9px] font-mono text-arkhe-purple/80">{log}</div>
                ))}
                {logs.length === 0 && <div className="text-[9px] font-mono text-arkhe-muted/50 italic">Awaiting initiation...</div>}
             </div>
          </div>

          <div className="flex items-center gap-4 p-4 bg-white/5 rounded border border-white/10">
             <div className="w-10 h-10 rounded-full flex items-center justify-center border border-arkhe-purple/50 bg-arkhe-purple/10">
                <ShieldCheck className="w-5 h-5 text-arkhe-purple" />
             </div>
             <div className="flex-1 min-w-0">
                <div className="text-xs font-mono font-bold text-arkhe-text uppercase">Last Genesis Seal</div>
                <div className="text-[9px] font-mono text-arkhe-muted truncate">{state.lastGenesisSeal}</div>
             </div>
          </div>

          <button
            onClick={handleGenerate}
            disabled={isGenerating}
            className="w-full py-3 bg-arkhe-purple/20 hover:bg-arkhe-purple/30 border border-arkhe-purple/50 rounded text-xs font-mono text-arkhe-purple transition-all uppercase tracking-widest font-bold shadow-[0_0_20px_rgba(168,85,247,0.2)] disabled:opacity-50"
          >
            {isGenerating ? 'Instantiating Reality...' : 'Initialize Reality Genesis'}
          </button>
        </div>
      </motion.div>
    </div>
  );
}
