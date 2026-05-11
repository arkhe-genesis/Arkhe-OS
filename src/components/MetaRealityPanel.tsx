
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

/* eslint-disable @typescript-eslint/no-unused-vars, no-shadow-restricted-names */


import { X, Box, Zap, AlertTriangle, Infinity } from 'lucide-react';
import { motion } from 'motion/react';
import React from 'react';

import type { MetaRealityState } from '../../server/types';

interface MetaRealityPanelProps {
  state?: MetaRealityState;
  onClose: () => void;
}

export default function MetaRealityPanel({ state, onClose }: MetaRealityPanelProps) {
  if (!state) { return null; }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-[#0a0a0c] border border-arkhe-cyan/30 rounded-xl w-full max-w-2xl overflow-hidden shadow-[0_0_30px_rgba(0,255,255,0.1)] flex flex-col"
      >
        <div className="p-4 border-b border-arkhe-cyan/20 flex justify-between items-center bg-arkhe-cyan/5">
          <div className="flex items-center gap-3">
            <Box className="w-5 h-5 text-arkhe-cyan" />
            <h2 className="font-mono text-sm uppercase tracking-widest text-arkhe-cyan font-bold">Meta-Reality Architecture</h2>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-black/40 p-4 rounded border border-white/5 space-y-1">
              <div className="text-[10px] text-arkhe-muted uppercase">Laws Violated</div>
              <div className="text-xl font-bold text-arkhe-red font-mono">{state.violatedLawsCount}</div>
            </div>
            <div className="bg-black/40 p-4 rounded border border-white/5 space-y-1">
              <div className="text-[10px] text-arkhe-muted uppercase">Stability Index</div>
              <div className="text-xl font-bold text-arkhe-cyan font-mono">{(state.metaStabilityIndex * 100).toFixed(1)}%</div>
            </div>
            <div className="bg-black/40 p-4 rounded border border-white/5 space-y-1">
              <div className="text-[10px] text-arkhe-muted uppercase">Imaginary Time</div>
              <div className="text-sm font-bold text-arkhe-text font-mono uppercase">{state.imaginaryTimeActive ? 'ACTIVE' : 'INACTIVE'}</div>
            </div>
          </div>

          <div className="bg-white/5 p-4 rounded border border-white/10 space-y-3">
             <div className="flex items-center gap-2 text-arkhe-cyan">
                <Infinity className="w-4 h-4" />
                <h3 className="text-xs font-mono font-bold uppercase">Non-Physical Manifolds</h3>
             </div>
             <div className="flex flex-wrap gap-2">
                {state.nonPhysicalManifolds.map((m, i) => (
                   <span key={i} className="px-2 py-1 bg-arkhe-cyan/10 border border-arkhe-cyan/30 text-arkhe-cyan text-[10px] font-mono rounded">
                      {m}
                   </span>
                ))}
                {state.nonPhysicalManifolds.length === 0 && (
                   <span className="text-[10px] font-mono text-arkhe-muted italic">No manifolds deployed beyond physical laws.</span>
                )}
             </div>
          </div>

          <div className="flex items-center gap-3 p-4 bg-arkhe-red/5 border border-arkhe-red/20 rounded">
             <AlertTriangle className="w-5 h-5 text-arkhe-red" />
             <div className="text-[10px] font-mono text-arkhe-muted">
                Warning: Deploying meta-reality systems may cause local ontological decoherence. Proceed with extreme caution.
             </div>
          </div>

          <button
            onClick={() => fetch('/api/metareality/deploy', { method: 'POST' })}
            className="w-full py-3 bg-arkhe-cyan/20 hover:bg-arkhe-cyan/30 border border-arkhe-cyan/50 rounded text-xs font-mono text-arkhe-cyan transition-all uppercase tracking-widest font-bold shadow-[0_0_20px_rgba(0,255,255,0.2)]"
          >
            Deploy Meta-Physical Manifold
          </button>
        </div>
      </motion.div>
    </div>
  );
}
