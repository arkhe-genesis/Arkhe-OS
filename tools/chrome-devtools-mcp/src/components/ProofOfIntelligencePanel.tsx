
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Brain, Share2, Shield, Zap, Activity, GitCommit, CheckCircle2, TrendingUp, X } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import React, { useState, useEffect } from 'react';

interface Experiment {
  id: string;
  type: 'mutation' | 'discovery' | 'benchmark';
  author: string;
  loss: number;
  adoptions: number;
  timestamp: string;
  verified: boolean;
}

interface ProofOfIntelligencePanelProps {
  onClose: () => void;
}

export default function ProofOfIntelligencePanel({ onClose }: ProofOfIntelligencePanelProps) {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [globalWeight, setGlobalWeight] = useState(1.0);

  useEffect(() => {
    // Simulated ResearchDAG feed
    const mockExperiments: Experiment[] = [
      { id: '0xf3a1', type: 'discovery', author: 'Agent-77', loss: 0.1242, adoptions: 12, timestamp: new Date().toISOString(), verified: true },
      { id: '0x11b9', type: 'mutation', author: 'Miner-Rio-01', loss: 0.1238, adoptions: 4, timestamp: new Date(Date.now() - 300000).toISOString(), verified: true },
      { id: '0xd992', type: 'benchmark', author: 'FullNode-Carioca', loss: 0.882, adoptions: 0, timestamp: new Date(Date.now() - 600000).toISOString(), verified: true },
    ];
    setExperiments(mockExperiments);

    const interval = setInterval(() => {
      setGlobalWeight(prev => prev + (Math.random() * 0.01 - 0.005));
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="fixed inset-0 bg-[#050507]/90 backdrop-blur-md z-50 flex items-center justify-center p-4 md:p-8">
      <div className="bg-[#101010] border border-[#3d3a39] rounded-lg w-full max-w-5xl h-[85vh] flex flex-col shadow-[0_20px_60px_rgba(0,0,0,0.7),inset_0_0_0_1px_rgba(148,163,184,0.1)] overflow-hidden relative">
        {/* Header */}
        <div className="p-6 border-b border-[#3d3a39] flex items-center justify-between bg-black/40">
          <div className="flex items-center space-x-3">
            <div className="relative">
              <Brain className="w-6 h-6 text-[#00d992]" />
              <div className="absolute inset-0 text-[#00d992] blur-sm opacity-50 animate-pulse"><Brain className="w-6 h-6" /></div>
            </div>
            <h2 className="text-xl font-[system-ui] font-bold text-[#f2f2f2] tracking-tight uppercase leading-[1.11]">Proof of Intelligence</h2>
          </div>
          <div className="flex items-center space-x-4">
            <div className="hidden md:flex flex-col items-end">
              <span className="text-[10px] font-mono text-[#8b949e] uppercase tracking-widest">Network Weight</span>
              <span className="text-sm font-mono text-[#00d992]">{globalWeight.toFixed(4)}x</span>
            </div>
            <button
              onClick={onClose}
              className="p-2 text-[#8b949e] hover:text-white transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-hidden flex flex-col md:flex-row">
          {/* Main Content - ResearchDAG */}
          <div className="flex-1 p-6 overflow-y-auto custom-scrollbar border-b md:border-b-0 md:border-r border-[#3d3a39]">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-sm font-[system-ui] font-bold text-[#f2f2f2] uppercase tracking-wider flex items-center gap-2">
                <GitCommit className="w-4 h-4 text-[#00d992]" />
                ResearchDAG Commits
              </h3>
              <div className="flex gap-2">
                <span className="px-2 py-0.5 rounded-full bg-[#00d992]/10 border border-[#00d992]/30 text-[9px] text-[#00d992] font-bold uppercase tracking-tighter">Live Feed</span>
              </div>
            </div>

            <div className="space-y-4">
              <AnimatePresence initial={false}>
                {experiments.map((exp) => (
                  <motion.div
                    key={exp.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="p-4 bg-black/30 border border-[#3d3a39] rounded-lg hover:border-[#00d992]/50 transition-all group"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex items-center gap-3">
                        <div className={`p-1.5 rounded bg-[#3d3a39]/50 ${exp.type === 'discovery' ? 'text-[#00d992]' : 'text-[#818cf8]'}`}>
                          {exp.type === 'discovery' ? <Zap className="w-4 h-4" /> : <TrendingUp className="w-4 h-4" />}
                        </div>
                        <div>
                          <div className="text-xs font-mono text-[#f2f2f2] font-bold">{exp.id}</div>
                          <div className="text-[10px] text-[#8b949e] font-mono">{exp.author}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-[10px] font-mono text-[#8b949e]">{new Date(exp.timestamp).toLocaleTimeString()}</div>
                        <div className="text-xs font-mono text-[#00d992] font-bold">-{exp.loss.toFixed(4)} Loss</div>
                      </div>
                    </div>
                    <div className="flex items-center justify-between pt-3 border-t border-[#3d3a39]/50">
                      <div className="flex items-center gap-4">
                        <div className="flex items-center gap-1 text-[10px] text-[#b8b3b0]">
                          <Share2 className="w-3 h-3 text-[#00d992]" />
                          {exp.adoptions} Adoptions
                        </div>
                        {exp.verified && (
                          <div className="flex items-center gap-1 text-[10px] text-[#00d992]">
                            <CheckCircle2 className="w-3 h-3" />
                            zkWASM Verified
                          </div>
                        )}
                      </div>
                      <button className="text-[9px] font-bold text-[#00d992] uppercase tracking-widest opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
                        Adopt <Share2 className="w-2.5 h-2.5" />
                      </button>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </div>

          {/* Sidebar - Adoption Economy & Proofs */}
          <div className="w-full md:w-80 p-6 space-y-8 bg-black/20 overflow-y-auto custom-scrollbar">
            {/* Multipliers */}
            <div>
              <h3 className="text-[10px] font-mono text-[#8b949e] uppercase tracking-[2.52px] font-bold mb-4">Adoption Multipliers</h3>
              <div className="space-y-2">
                {[
                  { role: 'Miner', mult: '4.0x', color: 'text-[#00d992]' },
                  { role: 'Full Node', mult: '2.0x', color: 'text-[#2fd6a1]' },
                  { role: 'Router', mult: '1.5x', color: 'text-[#8b949e]' },
                  { role: 'P2P Agent', mult: '1.25x', color: 'text-[#8b949e]' },
                ].map((m) => (
                  <div key={m.role} className="flex justify-between items-center p-2 rounded bg-[#3d3a39]/20 border border-[#3d3a39]/30">
                    <span className="text-[11px] font-mono text-[#b8b3b0]">{m.role}</span>
                    <span className={`text-[11px] font-mono font-bold ${m.color}`}>{m.mult}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Adoption Boosts */}
            <div>
              <h3 className="text-[10px] font-mono text-[#8b949e] uppercase tracking-[2.52px] font-bold mb-4">Weight Boosts</h3>
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-[#00d992]"></div>
                  <div className="flex-1 text-[10px] text-[#b8b3b0]">Experiment Completed</div>
                  <div className="text-[10px] font-mono text-[#00d992]">+0.1x</div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-[#00d992] shadow-[0_0_5px_#00d992]"></div>
                  <div className="flex-1 text-[10px] text-[#b8b3b0]">Another node adopts</div>
                  <div className="text-[10px] font-mono text-[#00d992]">+0.5x</div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-[#818cf8]"></div>
                  <div className="flex-1 text-[10px] text-[#b8b3b0]">Adopt & Improve</div>
                  <div className="text-[10px] font-mono text-[#818cf8]">+1.0x</div>
                </div>
              </div>
            </div>

            {/* Proofs Status */}
            <div className="pt-6 border-t border-[#3d3a39]">
              <h3 className="text-[10px] font-mono text-[#8b949e] uppercase tracking-[2.52px] font-bold mb-4">Verification Layer</h3>
              <div className="p-3 bg-black/40 rounded border border-[#3d3a39] space-y-4">
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-[9px] font-mono text-[#8b949e] uppercase">zkWASM (Plonky3)</span>
                    <span className="text-[9px] font-mono text-[#00d992]">SECURE</span>
                  </div>
                  <div className="h-1 bg-[#3d3a39] rounded-full overflow-hidden">
                    <div className="h-full bg-[#00d992] w-full shadow-[0_0_5px_#00d992]"></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-[9px] font-mono text-[#8b949e] uppercase">HSCP Spot-checks</span>
                    <span className="text-[9px] font-mono text-[#00d992]">99.9%</span>
                  </div>
                  <div className="h-1 bg-[#3d3a39] rounded-full overflow-hidden">
                    <div className="h-full bg-[#00d992] w-[99.9%]"></div>
                  </div>
                </div>
              </div>
            </div>

            {/* Performance */}
            <div className="p-3 bg-[#00d992]/5 border border-[#00d992]/20 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Activity className="w-3.5 h-3.5 text-[#00d992]" />
                <span className="text-[10px] font-bold text-[#f2f2f2] uppercase">Tempo UX Stats</span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div className="p-2 bg-black/40 rounded border border-[#3d3a39]">
                  <div className="text-[8px] text-[#8b949e] uppercase">P95 Latency</div>
                  <div className="text-xs font-mono text-[#00d992]">145ms</div>
                </div>
                <div className="p-2 bg-black/40 rounded border border-[#3d3a39]">
                  <div className="text-[8px] text-[#8b949e] uppercase">Throughput</div>
                  <div className="text-xs font-mono text-[#00d992]">8.4k QPS</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 bg-black/60 border-t border-[#3d3a39] flex items-center justify-between text-[9px] font-mono text-[#8b949e] uppercase tracking-widest">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1"><Shield className="w-3 h-3" /> A1 Chain v1.3.0</span>
            <span className="flex items-center gap-1"><GitCommit className="w-3 h-3" /> Block: 854,500</span>
          </div>
          <div className="flex items-center gap-1 text-[#00d992]">
            <Activity className="w-3 h-3 animate-pulse" />
            Synchronized
          </div>
        </div>
      </div>
    </div>
  );
}
