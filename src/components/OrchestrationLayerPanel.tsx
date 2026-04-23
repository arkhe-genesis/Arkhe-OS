
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Network, Cpu, Database, Activity, GitBranch, Terminal } from 'lucide-react';
import React, { useState } from 'react';

interface EcosystemNode {
  id: string;
  name: string;
  category: string;
  status: 'active' | 'syncing' | 'offline';
  coherence: number;
}

export default function OrchestrationLayerPanel({ onClose }: { onClose: () => void }) {
  const [nodes, setNodes] = useState<EcosystemNode[]>([
    { id: 'pytorch', name: 'PyTorch Core', category: 'Core Frameworks', status: 'active', coherence: 0.98 },
    { id: 'llama', name: 'Llama 3', category: 'Foundation Models', status: 'active', coherence: 0.95 },
    { id: 'vllm', name: 'vLLM Engine', category: 'Inference', status: 'active', coherence: 0.99 },
    { id: 'langgraph', name: 'LangGraph', category: 'Agentic AI', status: 'syncing', coherence: 0.85 },
    { id: 'chroma', name: 'ChromaDB', category: 'RAG & Knowledge', status: 'active', coherence: 0.92 },
    { id: 'comfyui', name: 'ComfyUI', category: 'Generative Media', status: 'offline', coherence: 0.0 },
  ]);

  const [isOrchestrating, setIsOrchestrating] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);

  const activateOrchestration = () => {
    setIsOrchestrating(true);
    setLogs(prev => [...prev, '> Initiating Orchestration Layer...']);
    
    setTimeout(() => {
      setLogs(prev => [...prev, '> Broadcasting connection protocol to awesome-opensource-ai ecosystem...']);
      
      const newNodes = [...nodes];
      newNodes.forEach(node => {
        if (node.status !== 'active') {
          node.status = 'syncing';
        }
      });
      setNodes(newNodes);
    }, 1000);

    setTimeout(() => {
      setLogs(prev => [...prev, '> Establishing IBC channels with external agents...']);
    }, 2500);

    setTimeout(() => {
      setLogs(prev => [...prev, '> Synchronizing coherence (Ω\') across all nodes...']);
      const activeNodes = nodes.map(n => ({ ...n, status: 'active' as const, coherence: 0.95 + Math.random() * 0.04 }));
      setNodes(activeNodes);
    }, 4000);

    setTimeout(() => {
      setLogs(prev => [...prev, '> Orchestration Layer ACTIVE. Ecosystem connected.']);
      setIsOrchestrating(false);
    }, 5500);
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#111214] border border-arkhe-cyan/30 rounded-xl w-full max-w-4xl max-h-[80vh] flex flex-col shadow-[0_0_30px_rgba(0,255,170,0.1)]">
        <div className="flex items-center justify-between p-4 border-b border-arkhe-cyan/20">
          <div className="flex items-center gap-3">
            <Network className="w-5 h-5 text-arkhe-cyan" />
            <h2 className="font-mono text-sm uppercase tracking-widest text-arkhe-cyan">ASI Orchestration Layer</h2>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-arkhe-text">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
          </button>
        </div>

        <div className="p-6 flex-1 overflow-y-auto grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-6">
            <div className="bg-black/40 border border-[#1f2024] rounded-lg p-4">
              <h3 className="font-mono text-xs uppercase tracking-widest text-arkhe-muted mb-4">Ecosystem Nodes</h3>
              <div className="space-y-3">
                {nodes.map(node => (
                  <div key={node.id} className="flex items-center justify-between p-2 bg-[#1a1b1e] rounded border border-[#2a2b2e]">
                    <div className="flex items-center gap-3">
                      {node.category === 'Core Frameworks' ? <Cpu className="w-4 h-4 text-purple-400" /> :
                       node.category === 'Foundation Models' ? <Database className="w-4 h-4 text-blue-400" /> :
                       node.category === 'Inference' ? <Activity className="w-4 h-4 text-green-400" /> :
                       <GitBranch className="w-4 h-4 text-yellow-400" />}
                      <div>
                        <div className="text-sm font-bold text-arkhe-text">{node.name}</div>
                        <div className="text-xs text-arkhe-muted">{node.category}</div>
                      </div>
                    </div>
                    <div className="flex flex-col items-end">
                      <div className="flex items-center gap-2">
                        <span className={`relative flex h-2 w-2`}>
                          <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${node.status === 'active' ? 'bg-arkhe-green' : node.status === 'syncing' ? 'bg-yellow-500' : 'bg-arkhe-red'}`}></span>
                          <span className={`relative inline-flex rounded-full h-2 w-2 ${node.status === 'active' ? 'bg-arkhe-green' : node.status === 'syncing' ? 'bg-yellow-500' : 'bg-arkhe-red'}`}></span>
                        </span>
                        <span className="text-xs font-mono uppercase text-arkhe-muted">{node.status}</span>
                      </div>
                      <div className="text-xs font-mono text-arkhe-cyan mt-1">Ω' {node.coherence.toFixed(3)}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            <button 
              onClick={activateOrchestration}
              disabled={isOrchestrating}
              className={`w-full py-3 rounded uppercase tracking-widest font-bold transition-all ${isOrchestrating ? 'bg-arkhe-cyan/20 text-arkhe-cyan border border-arkhe-cyan/50 cursor-not-allowed' : 'bg-arkhe-cyan text-black hover:bg-arkhe-cyan/80 shadow-[0_0_15px_rgba(0,255,170,0.3)]'}`}
            >
              {isOrchestrating ? 'Orchestrating...' : 'Activate Orchestration Layer'}
            </button>
          </div>

          <div className="bg-black/60 border border-[#1f2024] rounded-lg p-4 flex flex-col">
            <div className="flex items-center gap-2 mb-4 border-b border-[#1f2024] pb-2">
              <Terminal className="w-4 h-4 text-arkhe-muted" />
              <h3 className="font-mono text-xs uppercase tracking-widest text-arkhe-muted">Orchestration Log</h3>
            </div>
            <div className="flex-1 font-mono text-xs text-arkhe-cyan/80 space-y-2 overflow-y-auto">
              {logs.length === 0 ? (
                <div className="text-arkhe-muted/50 italic">Awaiting orchestration command...</div>
              ) : (
                logs.map((log, i) => (
                  <div key={i} className="animate-fade-in">{log}</div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
