
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Network, Brain, Shield, Zap, Clock,  Eye, Layers } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import React, { useState, useEffect } from 'react';

interface AgentNode {
  id: string;
  label: string;
  icon: React.ElementType;
  color: string;
  modules: string[];
  description: string;
}

const ontologyNodes: AgentNode[] = [
  {
    id: 'sensory',
    label: 'Agentes de Percepção (SENSORY)',
    icon: Eye,
    color: 'text-cyan-400',
    modules: ['CoherenceMonitor', 'AquiferSpectrogram', 'TzinorTerminal', 'ArkheVision'],
    description: 'Traduzem a realidade física (água, luz, fase) em vetores de informação quântica.'
  },
  {
    id: 'cognitive',
    label: 'Agentes de Cognição (COGNITIVE)',
    icon: Brain,
    color: 'text-purple-400',
    modules: ['IntelligenceHub', 'NeuralMolecularBridge', 'OrbVMRNAComputing', 'CollectiveIntelligence'],
    description: 'Processam a informação usando wetware e LLMs, gerando significado e intenção.'
  },
  {
    id: 'immune',
    label: 'Agentes de Imunidade (IMMUNE)',
    icon: Shield,
    color: 'text-emerald-400',
    modules: ['ThreatDetection', 'YangBaxterVerifier', 'ArkheSecTelemetry', 'ZkERCSimulator'],
    description: 'Protegem a integridade do sistema via ZK-Proofs, eBPF e topologia algébrica.'
  },
  {
    id: 'metabolic',
    label: 'Agentes de Metabolismo (METABOLIC)',
    icon: Zap,
    color: 'text-amber-400',
    modules: ['ThermodynamicsPanel', 'DysonSphereTelemetry', 'HardwareTelemetry', 'OrbitalCompute'],
    description: 'Gerenciam a energia, dissipação térmica e limites físicos do hardware.'
  },
  {
    id: 'temporal',
    label: 'Agentes de Ancoragem (TEMPORAL)',
    icon: Clock,
    color: 'text-blue-400',
    modules: ['TimechainVisualizer', 'ArkheChainPanel', 'ChronoCoilPanel', 'GenesisBlockSigner'],
    description: 'Ancoram o estado coerente no tempo e no espaço através de consenso distribuído.'
  }
];

export default function UnifiedOntologyPanel({ onClose }: { onClose?: () => void }) {
  const [activeNode, setActiveNode] = useState<string | null>(null);
  const [coherence, setCoherence] = useState(0.999);

  useEffect(() => {
    const interval = setInterval(() => {
      setCoherence(prev => Math.max(0.8, Math.min(1, prev + (Math.random() - 0.5) * 0.05)));
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-[#0a0a0c] border border-cyan-500/30 rounded-xl p-6 flex flex-col gap-6 relative overflow-hidden min-h-[600px]">
      <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/stardust.png')] opacity-5 pointer-events-none"></div>
      
      <div className="flex items-center justify-between border-b border-cyan-500/30 pb-3 relative z-10">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-cyan-500/10 rounded-lg border border-cyan-500/30">
            <Layers className="w-6 h-6 text-cyan-400" />
          </div>
          <div>
            <h2 className="font-mono text-lg uppercase tracking-widest text-cyan-400 font-bold">
              Ontologia Unificada Arkhe-Ω
            </h2>
            <div className="text-xs font-mono text-cyan-500/70 uppercase">
              Orquestração de Agentes Modulares
            </div>
          </div>
        </div>
        {onClose && (
          <button onClick={onClose} className="text-arkhe-muted hover:text-white font-mono text-xs">
            [X] CLOSE
          </button>
        )}
      </div>

      <div className="flex-1 flex flex-col lg:flex-row gap-8 relative z-10">
        {/* Grafo Ontológico */}
        <div className="flex-1 relative flex items-center justify-center min-h-[400px]">
          {/* Nó Central (A=A) */}
          <motion.div 
            className="absolute z-20 w-32 h-32 rounded-full bg-black border-2 border-cyan-400 flex flex-col items-center justify-center shadow-[0_0_30px_rgba(6,182,212,0.4)] cursor-pointer"
            animate={{ 
              boxShadow: ['0 0 20px rgba(6,182,212,0.2)', '0 0 50px rgba(6,182,212,0.6)', '0 0 20px rgba(6,182,212,0.2)'],
              scale: [1, 1.02, 1]
            }}
            transition={{ duration: 4, repeat: Infinity }}
            onClick={() => setActiveNode(null)}
          >
            <span className="text-3xl mb-1">🜏</span>
            <span className="font-mono text-xs font-bold text-cyan-400">ARKHE-Ω</span>
            <span className="font-mono text-[9px] text-cyan-500/70">λ₂ = {coherence.toFixed(4)}</span>
          </motion.div>

          {/* Nós Orbitais */}
          {ontologyNodes.map((node, index) => {
            const angle = (index * (360 / ontologyNodes.length)) * (Math.PI / 180);
            const radius = 160;
            const x = Math.cos(angle) * radius;
            const y = Math.sin(angle) * radius;
            const isActive = activeNode === node.id;
            const Icon = node.icon;

            return (
              <React.Fragment key={node.id}>
                {/* Linha de conexão */}
                <svg className="absolute inset-0 w-full h-full pointer-events-none z-0">
                  <motion.line 
                    x1="50%" y1="50%" 
                    x2={`calc(50% + ${x}px)`} y2={`calc(50% + ${y}px)`}
                    stroke={isActive ? 'rgba(6, 182, 212, 0.8)' : 'rgba(6, 182, 212, 0.2)'}
                    strokeWidth={isActive ? 2 : 1}
                    strokeDasharray={isActive ? "none" : "4 4"}
                    animate={{ strokeDashoffset: [0, 20] }}
                    transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                  />
                </svg>

                {/* Nó */}
                <motion.div
                  className={`absolute z-10 w-16 h-16 rounded-full bg-[#111214] border-2 flex items-center justify-center cursor-pointer transition-colors ${isActive ? 'border-white bg-white/10' : 'border-arkhe-border hover:border-cyan-500/50'}`}
                  style={{ x, y }}
                  whileHover={{ scale: 1.1 }}
                  onClick={() => setActiveNode(node.id)}
                >
                  <Icon className={`w-6 h-6 ${node.color}`} />
                </motion.div>
              </React.Fragment>
            );
          })}
        </div>

        {/* Painel de Detalhes da Ontologia */}
        <div className="w-full lg:w-80 bg-black/40 border border-cyan-500/20 rounded-lg p-4 flex flex-col">
          <h3 className="font-mono text-sm uppercase tracking-widest text-arkhe-muted mb-4 border-b border-arkhe-border pb-2">
            Definição Ontológica
          </h3>
          
          <AnimatePresence mode="wait">
            {activeNode ? (
              <motion.div 
                key={activeNode}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="flex flex-col gap-4"
              >
                {ontologyNodes.filter(n => n.id === activeNode).map(node => (
                  <div key={node.id} className="space-y-4">
                    <div className="flex items-center gap-2">
                      <node.icon className={`w-5 h-5 ${node.color}`} />
                      <h4 className={`font-mono text-sm font-bold ${node.color}`}>{node.label}</h4>
                    </div>
                    <p className="text-xs font-mono text-arkhe-muted leading-relaxed">
                      {node.description}
                    </p>
                    <div className="space-y-2">
                      <div className="text-[10px] font-mono uppercase text-cyan-500/70">Módulos (Agentes Instanciados):</div>
                      <ul className="space-y-1">
                        {node.modules.map(mod => (
                          <li key={mod} className="text-xs font-mono text-arkhe-text bg-white/5 px-2 py-1 rounded border border-white/10 flex items-center gap-2">
                            <div className={`w-1.5 h-1.5 rounded-full bg-current ${node.color}`}></div>
                            {mod}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                ))}
              </motion.div>
            ) : (
              <motion.div 
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex-1 flex flex-col items-center justify-center text-center gap-4 text-arkhe-muted"
              >
                <Network className="w-12 h-12 opacity-20" />
                <p className="text-xs font-mono">
                  Selecione uma classe de agentes no grafo para visualizar sua ontologia.
                </p>
                <div className="text-[10px] font-mono mt-4 p-3 bg-cyan-500/5 border border-cyan-500/20 rounded text-left">
                  <span className="text-cyan-400 font-bold">Axioma Fundamental:</span><br/>
                  Cada módulo da interface não é um componente passivo, mas um <strong>Agente Autônomo</strong>. A aplicação inteira é um enxame (swarm) orquestrado pelo Q-BGP, convergindo para a identidade A=A.
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
