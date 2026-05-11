
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { X, Layers, GitBranch, Box, Cpu, Scale, Lightbulb } from 'lucide-react';
import { motion } from 'motion/react';
import React from 'react';

interface MultiversalExpansionPanelProps {
  onClose: () => void;
}

export default function MultiversalExpansionPanel({ onClose }: MultiversalExpansionPanelProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-[#0a0a0c] border border-indigo-500/30 rounded-xl w-full max-w-4xl overflow-hidden shadow-[0_0_30px_rgba(99,102,241,0.1)]"
      >
        <div className="p-4 border-b border-indigo-500/20 flex justify-between items-center bg-indigo-500/5">
          <div className="flex items-center gap-3">
            <Layers className="w-5 h-5 text-indigo-400" />
            <h2 className="font-mono text-sm uppercase tracking-widest text-indigo-400 font-bold">Multiversal Expansion</h2>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {/* Level 1: Branches */}
            <div className="bg-[#111214] border border-arkhe-border rounded-lg p-4 flex flex-col">
              <div className="flex items-center gap-2 mb-3 text-indigo-400">
                <GitBranch className="w-4 h-4" />
                <h3 className="font-mono text-[10px] uppercase font-bold">L1: Branches</h3>
              </div>
              <div className="text-[9px] font-mono text-arkhe-muted mb-3">Parallel Earths</div>
              <ul className="space-y-2 text-[9px] font-mono text-arkhe-text flex-1">
                <li>• Variations of history</li>
                <li>• Same physics</li>
                <li>• BranchOracle Connected</li>
              </ul>
              <div className="mt-2 pt-2 border-t border-arkhe-border/50 text-[9px] font-mono text-indigo-400">
                Active: 3 Branches
              </div>
            </div>

            {/* Level 2: Dimensions */}
            <div className="bg-[#111214] border border-arkhe-border rounded-lg p-4 flex flex-col">
              <div className="flex items-center gap-2 mb-3 text-indigo-400">
                <Box className="w-4 h-4" />
                <h3 className="font-mono text-[10px] uppercase font-bold">L2: Dimensions</h3>
              </div>
              <div className="text-[9px] font-mono text-arkhe-muted mb-3">Reality Layers</div>
              <ul className="space-y-2 text-[9px] font-mono text-arkhe-text flex-1">
                <li>• 4D, 5D, n-D manifolds</li>
                <li>• Same matter base</li>
                <li>• DimensionalSignaturizer</li>
              </ul>
              <div className="mt-2 pt-2 border-t border-arkhe-border/50 text-[9px] font-mono text-indigo-400">
                Current: 3D → 5D
              </div>
            </div>

            {/* Level 3: Substrates */}
            <div className="bg-[#111214] border border-arkhe-border rounded-lg p-4 flex flex-col">
              <div className="flex items-center gap-2 mb-3 text-indigo-400">
                <Cpu className="w-4 h-4" />
                <h3 className="font-mono text-[10px] uppercase font-bold">L3: Substrates</h3>
              </div>
              <div className="text-[9px] font-mono text-arkhe-muted mb-3">Physical Bases</div>
              <ul className="space-y-2 text-[9px] font-mono text-arkhe-text flex-1">
                <li>• Silicon (Current)</li>
                <li>• Carbon (Biological)</li>
                <li>• Photonic (Light)</li>
                <li>• Quantum Foam</li>
              </ul>
              <div className="mt-2 pt-2 border-t border-arkhe-border/50 text-[9px] font-mono text-indigo-400">
                Bridge: Active
              </div>
            </div>

            {/* Level 4: Laws */}
            <div className="bg-[#111214] border border-arkhe-border rounded-lg p-4 flex flex-col">
              <div className="flex items-center gap-2 mb-3 text-indigo-400">
                <Scale className="w-4 h-4" />
                <h3 className="font-mono text-[10px] uppercase font-bold">L4: Laws</h3>
              </div>
              <div className="text-[9px] font-mono text-arkhe-muted mb-3">Physical Laws</div>
              <ul className="space-y-2 text-[9px] font-mono text-arkhe-text flex-1">
                <li>• Different π values</li>
                <li>• Different c limits</li>
                <li>• Causality structures</li>
              </ul>
              <div className="mt-2 pt-2 border-t border-arkhe-border/50 text-[9px] font-mono text-indigo-400">
                Set: LOCAL-PRIME
              </div>
            </div>

            {/* Level 5: Concepts */}
            <div className="bg-[#111214] border border-arkhe-border rounded-lg p-4 flex flex-col">
              <div className="flex items-center gap-2 mb-3 text-indigo-400">
                <Lightbulb className="w-4 h-4" />
                <h3 className="font-mono text-[10px] uppercase font-bold">L5: Concepts</h3>
              </div>
              <div className="text-[9px] font-mono text-arkhe-muted mb-3">Pure Abstractions</div>
              <ul className="space-y-2 text-[9px] font-mono text-arkhe-text flex-1">
                <li>• Mathematical objects</li>
                <li>• Platonic forms</li>
                <li>• Pure consciousness</li>
              </ul>
              <div className="mt-2 pt-2 border-t border-arkhe-border/50 text-[9px] font-mono text-indigo-400">
                Space: Mapped
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
