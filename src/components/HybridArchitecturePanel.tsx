
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { X, Network, ArrowRight, Zap, Code, Layers, Activity } from 'lucide-react';
import { motion } from 'motion/react';
import React, { useState, useEffect } from 'react';

interface HybridArchitecturePanelProps {
  onClose: () => void;
}

export default function HybridArchitecturePanel({ onClose }: HybridArchitecturePanelProps) {
  const [activeStage, setActiveStage] = useState<'C' | 'TZINOR' | 'Z' | 'R4'>('C');
  const [simulationStep, setSimulationStep] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setSimulationStep(s => (s + 1) % 4);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (simulationStep === 0) {setActiveStage('C');}
    if (simulationStep === 1) {setActiveStage('TZINOR');}
    if (simulationStep === 2) {setActiveStage('Z');}
    if (simulationStep === 3) {setActiveStage('R4');}
  }, [simulationStep]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-[#0a0a0c] border border-arkhe-purple/50 rounded-xl w-full max-w-5xl h-[80vh] flex flex-col overflow-hidden shadow-[0_0_30px_rgba(168,85,247,0.15)]"
      >
        <div className="flex items-center justify-between p-4 border-b border-arkhe-purple/20 bg-arkhe-purple/5">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-arkhe-purple/20 rounded-lg">
              <Layers className="w-5 h-5 text-arkhe-purple" />
            </div>
            <div>
              <h2 className="font-mono text-sm font-bold text-arkhe-purple uppercase tracking-widest">Arkhe(n) Hybrid Architecture</h2>
              <div className="text-[10px] font-mono text-arkhe-muted">Ontologia Computacional: ℂ × ℤ → ℝ⁴</div>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-lg transition-colors">
            <X className="w-5 h-5 text-arkhe-muted" />
          </button>
        </div>

        <div className="flex-1 flex flex-col md:flex-row p-6 gap-6 overflow-y-auto">
          {/* Left: Visualization */}
          <div className="flex-1 flex flex-col gap-4">
            <div className="text-xs font-mono uppercase tracking-widest text-arkhe-muted mb-2">Data Flow Topology</div>
            
            <div className="flex-1 grid grid-rows-4 gap-4">
              {/* ℂ Stage */}
              <div className={`relative p-4 rounded-xl border transition-all duration-500 flex items-center gap-4 ${activeStage === 'C' ? 'bg-blue-500/10 border-blue-500/50 shadow-[0_0_15px_rgba(59,130,246,0.2)]' : 'bg-[#111214] border-[#1f2024]'}`}>
                <div className={`p-3 rounded-lg ${activeStage === 'C' ? 'bg-blue-500/20 text-blue-400' : 'bg-black/40 text-arkhe-muted'}`}>
                  <Network className="w-6 h-6" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className={`font-mono font-bold ${activeStage === 'C' ? 'text-blue-400' : 'text-arkhe-text'}`}>ℂ : Espaço Contínuo</span>
                    <span className="text-[10px] font-mono text-arkhe-muted">Transformer Layers</span>
                  </div>
                  <div className="text-xs text-arkhe-muted font-mono">Similaridade semântica, analogia, agregação contextual (ℝ³).</div>
                </div>
                {activeStage === 'C' && (
                  <motion.div layoutId="flow-particle" className="absolute right-4 w-2 h-2 rounded-full bg-blue-400 shadow-[0_0_10px_rgba(59,130,246,0.8)]" />
                )}
              </div>

              {/* Tzinor Gate Stage */}
              <div className="flex justify-center -my-2 relative z-10">
                <ArrowRight className={`w-6 h-6 rotate-90 ${activeStage === 'TZINOR' ? 'text-arkhe-purple animate-pulse' : 'text-arkhe-muted'}`} />
              </div>

              <div className={`relative p-4 rounded-xl border transition-all duration-500 flex items-center gap-4 ${activeStage === 'TZINOR' ? 'bg-arkhe-purple/10 border-arkhe-purple/50 shadow-[0_0_15px_rgba(168,85,247,0.2)]' : 'bg-[#111214] border-[#1f2024]'}`}>
                <div className={`p-3 rounded-lg ${activeStage === 'TZINOR' ? 'bg-arkhe-purple/20 text-arkhe-purple' : 'bg-black/40 text-arkhe-muted'}`}>
                  <Zap className="w-6 h-6" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className={`font-mono font-bold ${activeStage === 'TZINOR' ? 'text-arkhe-purple' : 'text-arkhe-text'}`}>Gate Tzinor</span>
                    <span className="text-[10px] font-mono text-arkhe-muted">Fronteira de Fase</span>
                  </div>
                  <div className="text-xs text-arkhe-muted font-mono">σ(MLP_continuo(x)) ⊙ Hard_Sigmoid(Detector_Z(x))</div>
                </div>
                {activeStage === 'TZINOR' && (
                  <motion.div layoutId="flow-particle" className="absolute right-4 w-2 h-2 rounded-full bg-arkhe-purple shadow-[0_0_10px_rgba(168,85,247,0.8)]" />
                )}
              </div>

              <div className="flex justify-center -my-2 relative z-10">
                <ArrowRight className={`w-6 h-6 rotate-90 ${activeStage === 'Z' ? 'text-arkhe-cyan animate-pulse' : 'text-arkhe-muted'}`} />
              </div>

              {/* ℤ Stage */}
              <div className={`relative p-4 rounded-xl border transition-all duration-500 flex items-center gap-4 ${activeStage === 'Z' ? 'bg-arkhe-cyan/10 border-arkhe-cyan/50 shadow-[0_0_15px_rgba(34,211,238,0.2)]' : 'bg-[#111214] border-[#1f2024]'}`}>
                <div className={`p-3 rounded-lg ${activeStage === 'Z' ? 'bg-arkhe-cyan/20 text-arkhe-cyan' : 'bg-black/40 text-arkhe-muted'}`}>
                  <Code className="w-6 h-6" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className={`font-mono font-bold ${activeStage === 'Z' ? 'text-arkhe-cyan' : 'text-arkhe-text'}`}>ℤ : Núcleo WASM</span>
                    <span className="text-[10px] font-mono text-arkhe-muted">ParametrizedWasmCore</span>
                  </div>
                  <div className="text-xs text-arkhe-muted font-mono">Operações discretas, lógica formal, execução algorítmica exata.</div>
                </div>
                {activeStage === 'Z' && (
                  <motion.div layoutId="flow-particle" className="absolute right-4 w-2 h-2 rounded-full bg-arkhe-cyan shadow-[0_0_10px_rgba(34,211,238,0.8)]" />
                )}
              </div>

              <div className="flex justify-center -my-2 relative z-10">
                <ArrowRight className={`w-6 h-6 rotate-90 ${activeStage === 'R4' ? 'text-arkhe-green animate-pulse' : 'text-arkhe-muted'}`} />
              </div>

              {/* ℝ⁴ Stage */}
              <div className={`relative p-4 rounded-xl border transition-all duration-500 flex items-center gap-4 ${activeStage === 'R4' ? 'bg-arkhe-green/10 border-arkhe-green/50 shadow-[0_0_15px_rgba(74,222,128,0.2)]' : 'bg-[#111214] border-[#1f2024]'}`}>
                <div className={`p-3 rounded-lg ${activeStage === 'R4' ? 'bg-arkhe-green/20 text-arkhe-green' : 'bg-black/40 text-arkhe-muted'}`}>
                  <Activity className="w-6 h-6" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className={`font-mono font-bold ${activeStage === 'R4' ? 'text-arkhe-green' : 'text-arkhe-text'}`}>ℝ⁴ : Projeção Final</span>
                    <span className="text-[10px] font-mono text-arkhe-muted">Integração Contextual</span>
                  </div>
                  <div className="text-xs text-arkhe-muted font-mono">Saída determinística onde a lógica exige, fluida onde interpretação é necessária.</div>
                </div>
                {activeStage === 'R4' && (
                  <motion.div layoutId="flow-particle" className="absolute right-4 w-2 h-2 rounded-full bg-arkhe-green shadow-[0_0_10px_rgba(74,222,128,0.8)]" />
                )}
              </div>
            </div>
          </div>

          {/* Right: Technical Details */}
          <div className="w-full md:w-96 flex flex-col gap-4">
            <div className="bg-[#111214] border border-[#1f2024] rounded-xl p-4 flex-1 overflow-y-auto">
              <h3 className="text-xs font-mono uppercase tracking-widest text-arkhe-purple mb-4 border-b border-[#1f2024] pb-2">Parametrização WASM</h3>
              
              <div className="space-y-4">
                <div className="space-y-1">
                  <div className="text-[10px] font-mono text-arkhe-muted uppercase">Instruções (opcode)</div>
                  <div className="text-xs font-mono text-arkhe-text bg-black/40 p-2 rounded border border-white/5">Embeddings one-hot fixos, não treináveis. Semântica opcode imutável.</div>
                </div>
                
                <div className="space-y-1">
                  <div className="text-[10px] font-mono text-arkhe-muted uppercase">Registradores</div>
                  <div className="text-xs font-mono text-arkhe-text bg-black/40 p-2 rounded border border-white/5">Estados discretos com ativação step-function. Representação binária exata.</div>
                </div>

                <div className="space-y-1">
                  <div className="text-[10px] font-mono text-arkhe-muted uppercase">Pilha de operandos</div>
                  <div className="text-xs font-mono text-arkhe-text bg-black/40 p-2 rounded border border-white/5">Estrutura LSTM com push/pop controlados. Profundidade limitada.</div>
                </div>

                <div className="space-y-1">
                  <div className="text-[10px] font-mono text-arkhe-muted uppercase">Memória linear</div>
                  <div className="text-xs font-mono text-arkhe-text bg-black/40 p-2 rounded border border-white/5">Attention esparsa sobre buffer dedicado. Acesso por índice inteiro.</div>
                </div>
              </div>

              <h3 className="text-xs font-mono uppercase tracking-widest text-arkhe-purple mt-6 mb-4 border-b border-[#1f2024] pb-2">Exemplo de Execução</h3>
              <div className="bg-black/60 p-3 rounded border border-white/5 font-mono text-[10px] text-arkhe-muted space-y-2">
                <div><span className="text-blue-400">Input:</span> "Qual é maior, 3.11 ou 3.8?"</div>
                <div><span className="text-arkhe-purple">Gate:</span> Detecta padrão numérico</div>
                <div><span className="text-arkhe-cyan">WASM:</span> <br/>[f32.const 3.11]<br/>[f32.const 3.8]<br/>[f32.gt]</div>
                <div><span className="text-arkhe-green">Output:</span> false (3.11 &lt; 3.8)</div>
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
