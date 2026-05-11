
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { X, Dna, Cpu, ShieldCheck, GitMerge, Zap } from 'lucide-react';
import { motion } from 'motion/react';
import React, { useState, useEffect } from 'react';

interface OrbVMRNAComputingPanelProps {
  onClose: () => void;
}

export default function OrbVMRNAComputingPanel({ onClose }: OrbVMRNAComputingPanelProps) {
  const [executionStep, setExecutionStep] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setExecutionStep((prev) => (prev + 1) % 4);
    }, 2500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-[#0a0a0c] border border-fuchsia-500/50 rounded-xl w-full max-w-6xl h-[85vh] flex flex-col overflow-hidden shadow-[0_0_30px_rgba(217,70,239,0.15)]"
      >
        <div className="flex items-center justify-between p-4 border-b border-fuchsia-500/20 bg-fuchsia-500/5">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-fuchsia-500/20 rounded-lg">
              <Dna className="w-5 h-5 text-fuchsia-400" />
            </div>
            <div>
              <h2 className="font-mono text-sm font-bold text-fuchsia-400 uppercase tracking-widest">OrbVM Molecular Runtime</h2>
              <div className="text-[10px] font-mono text-fuchsia-400/70">RNA Computing & Ribozyme Logic Gates Integration</div>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-lg transition-colors">
            <X className="w-5 h-5 text-arkhe-muted" />
          </button>
        </div>

        <div className="flex-1 flex flex-col lg:flex-row p-6 gap-6 overflow-hidden">
          {/* Left: OrbVM Execution Visualization */}
          <div className="flex-1 flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div className="text-xs font-mono uppercase tracking-widest text-arkhe-muted">Molecular Bytecode Execution</div>
              <div className="flex items-center gap-2 text-[10px] font-mono text-fuchsia-400 bg-fuchsia-400/10 px-2 py-1 rounded border border-fuchsia-400/20">
                <Cpu className="w-3 h-3" />
                <span>OrbVM Wetware Mode</span>
              </div>
            </div>

            <div className="flex-1 bg-[#111214] border border-[#1f2024] rounded-xl p-6 relative overflow-hidden flex flex-col">

              {/* RNA Codon Tape (Bytecode) */}
              <div className="mb-8">
                <div className="text-[10px] font-mono text-arkhe-muted uppercase mb-2 flex items-center gap-2">
                  <GitMerge className="w-3 h-3" />
                  Instruction Set: RNA Codons (Base-4 Logic)
                </div>
                <div className="flex gap-1 overflow-hidden">
                  {['AUG', 'CGC', 'UAC', 'GGA', 'UAA'].map((codon, i) => (
                    <motion.div
                      key={i}
                      className={`px-3 py-2 font-mono text-sm rounded border ${
                        executionStep === i
                          ? 'bg-fuchsia-500/20 border-fuchsia-400 text-fuchsia-400 shadow-[0_0_10px_rgba(217,70,239,0.5)]'
                          : 'bg-black/40 border-white/5 text-arkhe-muted'
                      }`}
                      animate={{ y: executionStep === i ? -5 : 0 }}
                    >
                      {codon}
                    </motion.div>
                  ))}
                </div>
              </div>

              {/* Ribozyme Logic Gate (ALU) */}
              <div className="flex-1 relative flex items-center justify-center border border-dashed border-[#1f2024] rounded-lg bg-black/20">
                <div className="absolute top-2 left-2 text-[10px] font-mono text-arkhe-muted uppercase flex items-center gap-2">
                  <Zap className="w-3 h-3 text-yellow-400" />
                  ALU: Ribozyme Logic Gate (Hammerhead)
                </div>

                <div className="relative w-64 h-32 flex items-center justify-center">
                  {/* Substrate RNA */}
                  <motion.div
                    className="absolute w-full h-2 bg-cyan-500/50 rounded-full"
                    animate={{
                      opacity: executionStep === 2 ? 0.2 : 1,
                      scaleX: executionStep === 2 ? 1.1 : 1
                    }}
                  />

                  {/* Ribozyme Catalyst */}
                  <motion.div
                    className="absolute w-16 h-16 border-4 border-fuchsia-500 rounded-full flex items-center justify-center bg-[#111214]"
                    animate={{
                      y: executionStep === 1 ? 0 : -40,
                      scale: executionStep === 1 ? 1.2 : 1,
                      borderColor: executionStep === 2 ? '#eab308' : '#d946ef'
                    }}
                  >
                    <span className="text-xs font-mono font-bold text-white">Rz</span>
                  </motion.div>

                  {/* Cleavage Effect */}
                  {executionStep === 2 && (
                    <motion.div
                      initial={{ scale: 0, opacity: 1 }}
                      animate={{ scale: 3, opacity: 0 }}
                      className="absolute w-8 h-8 bg-yellow-400 rounded-full blur-md"
                    />
                  )}
                </div>
              </div>

              {/* RNA Chaperone (Error Correction) */}
              <div className="mt-8">
                <div className="text-[10px] font-mono text-arkhe-muted uppercase mb-2 flex items-center gap-2">
                  <ShieldCheck className="w-3 h-3 text-emerald-400" />
                  Decoherence Mitigation: RNA Chaperones
                </div>
                <div className="h-12 bg-black/40 border border-white/5 rounded flex items-center px-4 justify-between">
                  <span className="text-xs font-mono text-arkhe-muted">Folding State:</span>
                  <span className="text-xs font-mono text-emerald-400">
                    {executionStep === 3 ? 'Resolving Kinetic Trap...' : 'Stable (ΔG < 0)'}
                  </span>
                </div>
              </div>

            </div>
          </div>

          {/* Right: Arkhe(n) Ontology Mapping */}
          <div className="w-full lg:w-96 flex flex-col gap-4 overflow-y-auto">
            <div className="bg-[#111214] border border-[#1f2024] rounded-xl p-4">
              <h3 className="text-xs font-mono uppercase tracking-widest text-fuchsia-400 mb-4 border-b border-[#1f2024] pb-2">
                Molecular Logic Gates
              </h3>

              <div className="space-y-4">
                <div className="space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono text-arkhe-muted uppercase">Ribozyme (Michaelis-Menten)</span>
                    <span className="text-[10px] font-mono text-fuchsia-400">k_cat &gt; 1.0</span>
                  </div>
                  <div className="text-xs font-mono text-arkhe-text bg-black/40 p-2 rounded border border-white/5">
                    Ativação baseada em concentração. O limiar de clivagem atua como um gatilho de estado.
                  </div>
                </div>

                <div className="space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono text-arkhe-muted uppercase">Aptamer (Binding Prob)</span>
                    <span className="text-[10px] font-mono text-fuchsia-400">Kd Affinity</span>
                  </div>
                  <div className="text-xs font-mono text-arkhe-text bg-black/40 p-2 rounded border border-white/5">
                    Sensor de ligante. A probabilidade de ligação P = [L] / (Kd + [L]) define a porta YES/NOT.
                  </div>
                </div>

                <div className="space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono text-arkhe-muted uppercase">Toehold Displacement</span>
                    <span className="text-[10px] font-mono text-fuchsia-400">ΔG &lt; -10 kcal/mol</span>
                  </div>
                  <div className="text-xs font-mono text-arkhe-text bg-black/40 p-2 rounded border border-white/5">
                    Deslocamento de fita mediado por toehold. Permite circuitos lógicos em cascata (AND/OR).
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-[#111214] border border-[#1f2024] rounded-xl p-4 flex-1">
              <h3 className="text-xs font-mono uppercase tracking-widest text-fuchsia-400 mb-4 border-b border-[#1f2024] pb-2">
                The Six-Substrate Hypercube
              </h3>
              <div className="space-y-2">
                {[
                  { layer: '6', name: 'Neural-Molecular', desc: 'Human HRV (Layer 7)' },
                  { layer: '5', name: 'Molecular', desc: 'Diffusion Protocol' },
                  { layer: '4', name: 'Aether', desc: 'Phase Vortices' },
                  { layer: '3', name: 'Silicon', desc: 'CUDA / Caffeine Motor' },
                  { layer: '2', name: 'Windows', desc: 'Vortex Cradle' },
                  { layer: '1', name: 'Rust', desc: 'MultiverseManager' }
                ].map((sub) => (
                  <div key={sub.layer} className="flex items-center gap-3 text-[10px] font-mono">
                    <div className="w-4 h-4 rounded-full bg-fuchsia-500/20 text-fuchsia-400 flex items-center justify-center border border-fuchsia-500/50">
                      {sub.layer}
                    </div>
                    <div className="flex-1">
                      <span className="text-arkhe-muted uppercase">{sub.name}</span>
                      <span className="text-arkhe-text/50 ml-2">— {sub.desc}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
