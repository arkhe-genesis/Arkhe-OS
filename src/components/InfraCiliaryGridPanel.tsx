
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { X, Activity, Network, Dna, Waves, Zap } from 'lucide-react';
import { motion } from 'motion/react';
import React, { useState, useEffect } from 'react';

interface InfraCiliaryGridPanelProps {
  onClose: () => void;
}

const BEHAVIORS = [
  'Natação Helicoidal', 'Reação de Fuga', 'Forrageamento', 'Autofecundação',
  'Evitação de Obstáculos', 'Quimiotaxia Positiva', 'Quimiotaxia Negativa',
  'Termotaxia', 'Galvanotaxia', 'Tigmotaxia', 'Fototaxia', 'Geotaxia',
  'Conjugação', 'Endocitose', 'Exocitose', 'Contração Vacuolar', 'Descarga de Tricocistos'
];

export default function InfraCiliaryGridPanel({ onClose }: InfraCiliaryGridPanelProps) {
  const [activeBehavior, setActiveBehavior] = useState(0);
  const [phaseOffset, setPhaseOffset] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setPhaseOffset(p => (p + 0.1) % (Math.PI * 2));
    }, 50);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const behaviorInterval = setInterval(() => {
      setActiveBehavior(Math.floor(Math.random() * BEHAVIORS.length));
    }, 3000);
    return () => clearInterval(behaviorInterval);
  }, []);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-[#0a0a0c] border border-emerald-500/50 rounded-xl w-full max-w-6xl h-[85vh] flex flex-col overflow-hidden shadow-[0_0_30px_rgba(16,185,129,0.15)]"
      >
        <div className="flex items-center justify-between p-4 border-b border-emerald-500/20 bg-emerald-500/5">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-emerald-500/20 rounded-lg">
              <Dna className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <h2 className="font-mono text-sm font-bold text-emerald-400 uppercase tracking-widest">Infra-Ciliary Grid // Bio-Node Telemetry</h2>
              <div className="text-[10px] font-mono text-emerald-400/70">Paramecium Caudatum Microtubule Architecture (100k ℤ-Nodes)</div>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-lg transition-colors">
            <X className="w-5 h-5 text-arkhe-muted" />
          </button>
        </div>

        <div className="flex-1 flex flex-col lg:flex-row p-6 gap-6 overflow-hidden">
          {/* Left: Microtubule Grid Visualization */}
          <div className="flex-1 flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div className="text-xs font-mono uppercase tracking-widest text-arkhe-muted">Ondas Metacronais (Fase ℂ)</div>
              <div className="flex items-center gap-2 text-[10px] font-mono text-emerald-400 bg-emerald-400/10 px-2 py-1 rounded border border-emerald-400/20">
                <Waves className="w-3 h-3" />
                <span>Acoplamento de Fase Ativo</span>
              </div>
            </div>

            <div className="flex-1 bg-[#111214] border border-[#1f2024] rounded-xl p-6 relative overflow-hidden flex items-center justify-center">
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(16,185,129,0.05)_0%,transparent_70%)]" />

              {/* Grid of Microtubules */}
              <div className="grid grid-cols-12 gap-2 md:gap-4 relative z-10">
                {Array.from({ length: 144 }).map((_, i) => {
                  const x = i % 12;
                  const y = Math.floor(i / 12);
                  // Calculate wave phase based on position and time
                  const distance = Math.sqrt(Math.pow(x - 5.5, 2) + Math.pow(y - 5.5, 2));
                  const wave = Math.sin(distance * 0.8 - phaseOffset * 2);
                  const isActive = wave > 0.5;

                  return (
                    <motion.div
                      key={i}
                      className={`w-2 h-2 md:w-3 md:h-3 rounded-full ${isActive ? 'bg-emerald-400 shadow-[0_0_10px_rgba(16,185,129,0.8)]' : 'bg-[#1f2024]'}`}
                      animate={{
                        scale: isActive ? 1.5 : 1,
                        opacity: isActive ? 1 : 0.3
                      }}
                      transition={{ duration: 0.1 }}
                    />
                  );
                })}
              </div>

              {/* Overlay connecting lines (Tzinorot) */}
              <svg className="absolute inset-0 w-full h-full opacity-20 pointer-events-none">
                <defs>
                  <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                    <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#10b981" strokeWidth="0.5"/>
                  </pattern>
                </defs>
                <rect width="100%" height="100%" fill="url(#grid)" />
              </svg>
            </div>
          </div>

          {/* Right: Telemetry & Projections */}
          <div className="w-full lg:w-96 flex flex-col gap-4 overflow-y-auto">
            {/* Projeções R4 */}
            <div className="bg-[#111214] border border-[#1f2024] rounded-xl p-4">
              <h3 className="text-xs font-mono uppercase tracking-widest text-emerald-400 mb-4 border-b border-[#1f2024] pb-2 flex items-center gap-2">
                <Activity className="w-4 h-4" />
                Projeções ℝ⁴ (Comportamentos)
              </h3>
              <div className="grid grid-cols-2 gap-2">
                {BEHAVIORS.map((behavior, idx) => (
                  <div
                    key={behavior}
                    className={`text-[9px] font-mono px-2 py-1.5 rounded border transition-colors ${
                      idx === activeBehavior
                        ? 'bg-emerald-400/20 border-emerald-400 text-emerald-400 shadow-[0_0_10px_rgba(16,185,129,0.2)]'
                        : 'bg-black/40 border-white/5 text-arkhe-muted'
                    }`}
                  >
                    {behavior}
                  </div>
                ))}
              </div>
            </div>

            {/* Ontologia Estrutural */}
            <div className="bg-[#111214] border border-[#1f2024] rounded-xl p-4 flex-1">
              <h3 className="text-xs font-mono uppercase tracking-widest text-emerald-400 mb-4 border-b border-[#1f2024] pb-2 flex items-center gap-2">
                <Network className="w-4 h-4" />
                Mapeamento Ontológico
              </h3>

              <div className="space-y-4">
                <div className="space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono text-arkhe-muted uppercase">Estrutura ℤ</span>
                    <span className="text-[10px] font-mono text-emerald-400">100,000 Nós</span>
                  </div>
                  <div className="text-xs font-mono text-arkhe-text bg-black/40 p-2 rounded border border-white/5">
                    <span className="text-emerald-400 font-bold">Microtúbulos:</span> Discretização do espaço celular. Bits físicos da computação biológica.
                  </div>
                </div>

                <div className="space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono text-arkhe-muted uppercase">Tzinorot (Canais)</span>
                    <span className="text-[10px] font-mono text-emerald-400">Grade Infra-ciliar</span>
                  </div>
                  <div className="text-xs font-mono text-arkhe-text bg-black/40 p-2 rounded border border-white/5">
                    <span className="text-emerald-400 font-bold">Conexões:</span> Topologia de grafo ativo que permite a propagação da fase ℂ.
                  </div>
                </div>

                <div className="space-y-1">
                  <div className="text-[10px] font-mono text-arkhe-muted uppercase">Conexões Híbridas</div>
                  <div className="grid grid-cols-2 gap-2 mt-1">
                    <div className="bg-black/40 p-2 rounded border border-white/5">
                      <div className="text-[9px] text-emerald-400 mb-1">Hinductor</div>
                      <div className="text-[9px] text-arkhe-muted">Vórtices de corrente</div>
                    </div>
                    <div className="bg-black/40 p-2 rounded border border-white/5">
                      <div className="text-[9px] text-emerald-400 mb-1">Hadrônica</div>
                      <div className="text-[9px] text-arkhe-muted">Configuração de Quarks</div>
                    </div>
                  </div>
                </div>

                <div className="mt-4 p-3 bg-emerald-400/5 border border-emerald-400/20 rounded-lg">
                  <div className="flex items-start gap-2">
                    <Zap className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />
                    <p className="text-[10px] font-mono text-emerald-400/90 leading-relaxed">
                      "O neurônio não inventou a computação. Ele herdou os microtúbulos." A inteligência emerge da estrutura e coerência, não da centralização.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
