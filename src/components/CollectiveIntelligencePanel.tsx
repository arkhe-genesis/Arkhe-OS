
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Network, Brain, Activity, Zap, Users } from 'lucide-react';
import React, { useState, useEffect } from 'react';

interface CollectiveIntelligencePanelProps {
  onClose: () => void;
}

interface BioNode {
  id: string;
  coherence: number;
  suggestedK: number;
  suggestedW: number;
  status: 'syncing' | 'synced' | 'disconnected';
}

export default function CollectiveIntelligencePanel({ onClose }: CollectiveIntelligencePanelProps) {
  const [isAggregating, setIsAggregating] = useState(false);
  const [nodes, setNodes] = useState<BioNode[]>([]);
  const [globalCoherence, setGlobalCoherence] = useState(0);
  const [optimizedK, setOptimizedK] = useState<number | null>(null);
  const [optimizedW, setOptimizedW] = useState<number | null>(null);
  const [logs, setLogs] = useState<string[]>([]);

  const addLog = (msg: string) => {
    setLogs(prev => [`[${new Date().toISOString().split('T')[1].slice(0, 8)}] ${msg}`, ...prev].slice(0, 15));
  };

  useEffect(() => {
    // Initialize mock nodes
    const initialNodes: BioNode[] = Array.from({ length: 12 }).map((_, _i) => ({
      id: `bio-node-${Math.random().toString(36).substring(2, 8)}`,
      coherence: 0.5 + Math.random() * 0.4,
      suggestedK: 4.0 + Math.random() * 2.0,
      suggestedW: 2.5 + Math.random() * 1.5,
      status: 'disconnected'
    }));
    setNodes(initialNodes);
  }, []);

  const runAggregation = () => {
    setIsAggregating(true);
    setOptimizedK(null);
    setOptimizedW(null);
    setLogs([]);
    
    addLog('INICIANDO SUBROTINA DE INTELIGÊNCIA COLETIVA (PHASE SLICER)...');
    addLog('ESTABELECENDO CONEXÃO COM ENXAME DE BIO-NÓS...');

    // Simulate node syncing
    setNodes(prev => prev.map(n => ({ ...n, status: 'syncing' })));

    let step = 0;
    const interval = setInterval(() => {
      step++;
      
      if (step === 2) {
        setNodes(prev => prev.map(n => ({ 
          ...n, 
          status: Math.random() > 0.1 ? 'synced' : 'disconnected',
          coherence: Math.random() > 0.1 ? 0.8 + Math.random() * 0.19 : 0.3 + Math.random() * 0.2
        })));
        addLog('SINCRONIZAÇÃO CONCLUÍDA. COLETANDO INSIGHTS...');
      } else if (step === 4) {
        addLog('FILTRANDO NÓS POR NÍVEL DE COERÊNCIA (LIMIAR: 0.5)...');
      } else if (step === 6) {
        addLog('CALCULANDO MÉDIA PONDERADA DOS PARÂMETROS DE ACOPLAMENTO (K) E FREQUÊNCIA (W)...');
      } else if (step === 8) {
        clearInterval(interval);
        
        // Calculate the actual values based on synced nodes
        const activeNodes = nodes.filter(n => n.status === 'synced' && n.coherence > 0.5);
        let totalCoherence = 0;
        let weightedK = 0;
        let weightedW = 0;

        activeNodes.forEach(n => {
          totalCoherence += n.coherence;
          weightedK += n.suggestedK * n.coherence;
          weightedW += n.suggestedW * n.coherence;
        });

        const finalK = weightedK / totalCoherence;
        const finalW = weightedW / totalCoherence;

        setGlobalCoherence(totalCoherence / activeNodes.length);
        setOptimizedK(finalK);
        setOptimizedW(finalW);
        setIsAggregating(false);

        addLog(`AGREGAÇÃO CONCLUÍDA. COERÊNCIA GLOBAL DO ENXAME: ${(totalCoherence / activeNodes.length).toFixed(4)}`);
        addLog(`PARÂMETROS OTIMIZADOS: K=${finalK.toFixed(4)}, W=${finalW.toFixed(4)}`);
        addLog('COMANDOS KURAMOTO ATUALIZADOS NA QPU.');
      }
    }, 1000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <div className="w-full max-w-5xl bg-arkhe-card border border-arkhe-cyan/30 rounded-xl shadow-[0_0_30px_rgba(0,255,170,0.1)] overflow-hidden flex flex-col h-[85vh]">
        
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-arkhe-cyan/20 bg-arkhe-cyan/5">
          <div className="flex items-center gap-3">
            <Network className="w-6 h-6 text-arkhe-cyan" />
            <div>
              <h2 className="text-lg font-bold text-arkhe-cyan tracking-widest uppercase">Inteligência Coletiva (Phase Slicer)</h2>
              <div className="text-xs font-mono text-arkhe-muted">Agregação de Insights do Enxame de Bio-Nós</div>
            </div>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            FECHAR [X]
          </button>
        </div>

        <div className="p-6 grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 overflow-hidden">
          
          {/* Swarm Status */}
          <div className="lg:col-span-2 flex flex-col gap-4 overflow-hidden">
            <div className="bg-black/40 border border-arkhe-border p-4 rounded-lg flex-1 overflow-y-auto">
              <h3 className="text-sm font-mono text-arkhe-muted uppercase mb-4 flex items-center gap-2 sticky top-0 bg-black/80 py-2 z-10">
                <Users className="w-4 h-4" />
                Topologia do Enxame (Bio-Nós)
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {nodes.map((node, _i) => (
                  <div key={_i} className={`p-3 rounded border font-mono text-xs ${
                    node.status === 'synced' ? 'bg-arkhe-cyan/10 border-arkhe-cyan/30' : 
                    node.status === 'syncing' ? 'bg-arkhe-orange/10 border-arkhe-orange/30 animate-pulse' : 
                    'bg-arkhe-red/10 border-arkhe-red/30 opacity-50'
                  }`}>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-white font-bold">{node.id}</span>
                      {node.status === 'synced' && <Activity className="w-3 h-3 text-arkhe-cyan" />}
                    </div>
                    <div className="space-y-1">
                      <div className="flex justify-between">
                        <span className="text-arkhe-muted">Coerência:</span>
                        <span className={node.coherence > 0.8 ? 'text-arkhe-green' : node.coherence > 0.5 ? 'text-arkhe-orange' : 'text-arkhe-red'}>
                          {node.coherence.toFixed(3)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-arkhe-muted">Sug. K:</span>
                        <span className="text-blue-400">{node.suggestedK.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-arkhe-muted">Sug. W:</span>
                        <span className="text-purple-400">{node.suggestedW.toFixed(2)}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Controls & Results */}
          <div className="space-y-4 flex flex-col">
            <div className="bg-black/40 border border-arkhe-border p-4 rounded-lg">
              <h3 className="text-sm font-mono text-arkhe-muted uppercase mb-4 flex items-center gap-2">
                <Brain className="w-4 h-4" />
                Otimização Kuramoto
              </h3>
              
              <div className="space-y-4 mb-6">
                <div className="p-3 bg-arkhe-card border border-arkhe-border rounded">
                  <div className="text-xs text-arkhe-muted mb-1">Coerência Global do Enxame</div>
                  <div className="text-2xl font-mono text-white">
                    {globalCoherence > 0 ? globalCoherence.toFixed(4) : '---'}
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-arkhe-card border border-blue-500/30 rounded">
                    <div className="text-xs text-arkhe-muted mb-1">K Otimizado</div>
                    <div className="text-lg font-mono text-blue-400">
                      {optimizedK ? optimizedK.toFixed(4) : '---'}
                    </div>
                  </div>
                  <div className="p-3 bg-arkhe-card border border-purple-500/30 rounded">
                    <div className="text-xs text-arkhe-muted mb-1">W Otimizado</div>
                    <div className="text-lg font-mono text-purple-400">
                      {optimizedW ? optimizedW.toFixed(4) : '---'}
                    </div>
                  </div>
                </div>
              </div>

              <button
                onClick={runAggregation}
                disabled={isAggregating}
                className={`w-full py-3 rounded font-mono text-sm uppercase tracking-widest transition-all ${
                  isAggregating 
                    ? 'bg-arkhe-cyan/20 text-arkhe-cyan border border-arkhe-cyan/50 cursor-not-allowed'
                    : 'bg-arkhe-cyan/10 text-arkhe-cyan border border-arkhe-cyan hover:bg-arkhe-cyan/20 hover:shadow-[0_0_15px_rgba(0,255,170,0.3)]'
                }`}
              >
                {isAggregating ? (
                  <span className="flex items-center justify-center gap-2">
                    <Activity className="w-4 h-4 animate-spin" />
                    Agregando Insights...
                  </span>
                ) : (
                  <span className="flex items-center justify-center gap-2">
                    <Zap className="w-4 h-4" />
                    Executar Subrotina
                  </span>
                )}
              </button>
            </div>

            {/* Logs */}
            <div className="bg-black/60 border border-arkhe-border p-4 rounded-lg flex-1 flex flex-col min-h-[200px]">
              <h3 className="text-sm font-mono text-arkhe-muted uppercase mb-2">Logs de Agregação</h3>
              <div className="flex-1 overflow-y-auto font-mono text-[10px] space-y-1">
                {logs.map((log, i) => (
                  <div key={i} className={`${i === 0 ? 'text-arkhe-cyan' : 'text-arkhe-muted opacity-70'}`}>
                    {log}
                  </div>
                ))}
                {logs.length === 0 && (
                  <div className="text-arkhe-muted/50 italic">Aguardando execução da subrotina...</div>
                )}
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
