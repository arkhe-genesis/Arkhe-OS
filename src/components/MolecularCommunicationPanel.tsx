
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { X, Radio, Atom, Share2, Activity, Waves } from 'lucide-react';
import { motion } from 'motion/react';
import React, { useState, useEffect } from 'react';

interface MolecularCommunicationPanelProps {
  onClose: () => void;
}

const FRACTAL_SCALES = [
  { scale: 'Subatômica', substrate: 'Quarks', field: 'Força Forte', engineering: 'Hadrônica Retrocausal' },
  { scale: 'Molecular', substrate: 'Moléculas', field: 'Difusão', engineering: 'Comunicação Molecular' },
  { scale: 'Celular', substrate: 'Microtúbulos', field: 'Bioquímica', engineering: 'Biologia Sintética' },
  { scale: 'Organísmica', substrate: 'Neurônios', field: 'Elétrica', engineering: 'Neurociência' },
  { scale: 'Social', substrate: 'Humanos', field: 'Linguagem', engineering: 'Web3, IA' }
];

export default function MolecularCommunicationPanel({ onClose }: MolecularCommunicationPanelProps) {
  const [particles, setParticles] = useState<Array<{ id: number; delay: number; duration: number; yOffset: number }>>([]);

  useEffect(() => {
    // Generate random particles for the diffusion simulation
    const newParticles = Array.from({ length: 40 }).map((_, i) => ({
      id: i,
      delay: Math.random() * 5,
      duration: 3 + Math.random() * 4,
      yOffset: (Math.random() - 0.5) * 100 // Random vertical drift
    }));
    setParticles(newParticles);
  }, []);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-[#0a0a0c] border border-cyan-500/50 rounded-xl w-full max-w-6xl h-[85vh] flex flex-col overflow-hidden shadow-[0_0_30px_rgba(6,182,212,0.15)]"
      >
        <div className="flex items-center justify-between p-4 border-b border-cyan-500/20 bg-cyan-500/5">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-cyan-500/20 rounded-lg">
              <Atom className="w-5 h-5 text-cyan-400" />
            </div>
            <div>
              <h2 className="font-mono text-sm font-bold text-cyan-400 uppercase tracking-widest">IoNT & Molecular Communication // 6G Hybrid Layer</h2>
              <div className="text-[10px] font-mono text-cyan-400/70">Prof. LIN Lin (Tongji University) Research Telemetry</div>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-lg transition-colors">
            <X className="w-5 h-5 text-arkhe-muted" />
          </button>
        </div>

        <div className="flex-1 flex flex-col lg:flex-row p-6 gap-6 overflow-hidden">
          {/* Left: Molecular Diffusion Visualization */}
          <div className="flex-1 flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div className="text-xs font-mono uppercase tracking-widest text-arkhe-muted">Canal de Difusão Molecular (Tzinor)</div>
              <div className="flex items-center gap-2 text-[10px] font-mono text-cyan-400 bg-cyan-400/10 px-2 py-1 rounded border border-cyan-400/20">
                <Radio className="w-3 h-3" />
                <span>Transmissão 6G Wave-Denied Ativa</span>
              </div>
            </div>

            <div className="flex-1 bg-[#111214] border border-[#1f2024] rounded-xl p-6 relative overflow-hidden flex flex-col justify-center">
              <div className="absolute inset-0 bg-[linear-gradient(90deg,rgba(6,182,212,0.05)_0%,transparent_100%)]" />

              <div className="relative w-full h-64 flex items-center justify-between px-8">
                {/* Transmitter (Tx) */}
                <div className="relative z-10 flex flex-col items-center gap-2">
                  <div className="w-12 h-12 rounded-full border-2 border-cyan-400 bg-cyan-400/20 flex items-center justify-center shadow-[0_0_15px_rgba(6,182,212,0.5)]">
                    <span className="font-mono text-xs font-bold text-cyan-400">Tx</span>
                  </div>
                  <span className="text-[10px] font-mono text-arkhe-muted">Emissor (Estrutura ℤ)</span>
                </div>

                {/* Diffusion Channel */}
                <div className="absolute left-24 right-24 top-0 bottom-0 overflow-hidden">
                  {particles.map((p) => (
                    <motion.div
                      key={p.id}
                      className="absolute left-0 top-1/2 w-2 h-2 rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(6,182,212,0.8)]"
                      initial={{ x: 0, y: 0, opacity: 0, scale: 0 }}
                      animate={{
                        x: ['0%', '100%'],
                        y: [0, p.yOffset, p.yOffset * 1.5, p.yOffset * 0.5],
                        opacity: [0, 1, 1, 0],
                        scale: [0, 1, 1.5, 0.5]
                      }}
                      transition={{
                        duration: p.duration,
                        repeat: Infinity,
                        delay: p.delay,
                        ease: "linear"
                      }}
                    />
                  ))}
                </div>

                {/* Receiver (Rx) */}
                <div className="relative z-10 flex flex-col items-center gap-2">
                  <div className="w-12 h-12 rounded-full border-2 border-purple-400 bg-purple-400/20 flex items-center justify-center shadow-[0_0_15px_rgba(168,85,247,0.5)]">
                    <span className="font-mono text-xs font-bold text-purple-400">Rx</span>
                  </div>
                  <span className="text-[10px] font-mono text-arkhe-muted">Receptor (Projeção ℝ⁴)</span>
                </div>
              </div>

              <div className="mt-8 grid grid-cols-4 gap-4 text-center">
                <div className="bg-black/40 p-2 rounded border border-white/5">
                  <div className="text-[10px] font-mono text-arkhe-muted mb-1">Fase ℂ</div>
                  <div className="text-xs font-mono text-cyan-400">Pacotes Químicos</div>
                </div>
                <div className="bg-black/40 p-2 rounded border border-white/5">
                  <div className="text-[10px] font-mono text-arkhe-muted mb-1">Espaço ℝ³</div>
                  <div className="text-xs font-mono text-cyan-400">Meio Fluido</div>
                </div>
                <div className="bg-black/40 p-2 rounded border border-white/5">
                  <div className="text-[10px] font-mono text-arkhe-muted mb-1">Estrutura ℤ</div>
                  <div className="text-xs font-mono text-cyan-400">Concentração/Timing</div>
                </div>
                <div className="bg-black/40 p-2 rounded border border-white/5">
                  <div className="text-[10px] font-mono text-arkhe-muted mb-1">Projeção ℝ⁴</div>
                  <div className="text-xs font-mono text-purple-400">Ligação ao Receptor</div>
                </div>
              </div>
            </div>
          </div>

          {/* Right: Telemetry & Ontology */}
          <div className="w-full lg:w-96 flex flex-col gap-4 overflow-y-auto">
            {/* Sincronização Retrocausal */}
            <div className="bg-[#111214] border border-[#1f2024] rounded-xl p-4">
              <h3 className="text-xs font-mono uppercase tracking-widest text-cyan-400 mb-4 border-b border-[#1f2024] pb-2 flex items-center gap-2">
                <Activity className="w-4 h-4" />
                Sincronização Retrocausal
              </h3>
              <p className="text-[10px] font-mono text-arkhe-muted leading-relaxed mb-3">
                O atraso devido à difusão exige que a ação futura seja prevista e preparada no presente. O protocolo de sincronização atua como um Tzinor temporal entre nanomáquinas.
              </p>
              <div className="flex items-center justify-between bg-black/40 p-2 rounded border border-white/5">
                <span className="text-[10px] font-mono text-arkhe-muted">Coerência de Fase ℂ</span>
                <span className="text-[10px] font-mono text-cyan-400 animate-pulse">Sincronizada</span>
              </div>
            </div>

            {/* Escala Fractal de Informação */}
            <div className="bg-[#111214] border border-[#1f2024] rounded-xl p-4 flex-1">
              <h3 className="text-xs font-mono uppercase tracking-widest text-cyan-400 mb-4 border-b border-[#1f2024] pb-2 flex items-center gap-2">
                <Share2 className="w-4 h-4" />
                Escala Fractal de Informação
              </h3>

              <div className="space-y-2">
                <div className="grid grid-cols-4 gap-2 text-[9px] font-mono text-arkhe-muted uppercase border-b border-white/5 pb-1">
                  <div>Escala</div>
                  <div>Substrato</div>
                  <div>Campo</div>
                  <div>Engenharia</div>
                </div>
                {FRACTAL_SCALES.map((item, idx) => (
                  <div key={idx} className={`grid grid-cols-4 gap-2 text-[10px] font-mono p-1.5 rounded ${idx === 1 ? 'bg-cyan-400/10 border border-cyan-400/20 text-cyan-400' : 'text-arkhe-text hover:bg-white/5'}`}>
                    <div className={idx === 1 ? 'font-bold' : ''}>{item.scale}</div>
                    <div>{item.substrate}</div>
                    <div>{item.field}</div>
                    <div className="truncate" title={item.engineering}>{item.engineering}</div>
                  </div>
                ))}
              </div>

              <div className="mt-6 p-3 bg-cyan-400/5 border border-cyan-400/20 rounded-lg">
                <div className="flex items-start gap-2">
                  <Waves className="w-4 h-4 text-cyan-400 mt-0.5 shrink-0" />
                  <p className="text-[10px] font-mono text-cyan-400/90 leading-relaxed">
                    A Internet das Nanocoisas (IoNT) forma uma malha ℤ cobrindo a biologia. A comunicação molecular é a ponte entre a biologia do Paramecium e a engenharia de redes 6G.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
