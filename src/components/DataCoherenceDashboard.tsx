
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { X, Database, Activity, AlertCircle, RefreshCcw,  Shield, Network, Server } from 'lucide-react';
import { motion } from 'motion/react';
import React from 'react';

import type { SimulationState } from '../../server/types';
import { useArkheSimulation } from '../hooks/useArkheSimulation';

interface DataCoherenceDashboardProps {
  onClose: () => void;
}

export default function DataCoherenceDashboard({ onClose }: DataCoherenceDashboardProps) {
  const state: any = useArkheSimulation();
  const { domains, overallHealth } = state.scaData;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-[#0a0a0c] border border-blue-500/30 rounded-xl w-full max-w-4xl overflow-hidden shadow-[0_0_50px_rgba(59,130,246,0.15)] flex flex-col"
      >
        {/* Header */}
        <div className="p-4 border-b border-blue-500/20 flex justify-between items-center bg-blue-500/5">
          <div className="flex items-center gap-3">
            <Database className="w-5 h-5 text-blue-400" />
            <h2 className="font-mono text-sm uppercase tracking-widest text-blue-400 font-bold">
              SCA-Data: Arkhe Data Coherence Platform
            </h2>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 grid grid-cols-1 md:grid-cols-3 gap-6 overflow-y-auto max-h-[80vh] custom-scrollbar">
          {/* Main Score */}
          <div className="md:col-span-2 space-y-6">
            <div className="bg-white/5 border border-white/10 rounded-lg p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-xs font-mono uppercase tracking-widest text-arkhe-muted">Overall System Health (λ₂-data)</h3>
                <span className="text-2xl font-bold font-mono text-blue-400">{(overallHealth * 100).toFixed(1)}%</span>
              </div>
              <div className="w-full bg-white/5 h-4 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-blue-500"
                  animate={{ width: `${overallHealth * 100}%` }}
                />
              </div>
            </div>

            <div className="bg-white/5 border border-white/10 rounded-lg p-4">
              <h3 className="text-[10px] font-mono uppercase tracking-widest text-arkhe-muted mb-4 flex items-center gap-2">
                <Network className="w-3 h-3" />
                Network Infrastructure Layer
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-6">
                <div className="bg-black/40 border border-white/5 p-3 rounded">
                  <div className="flex justify-between items-start mb-1">
                    <span className="text-[8px] font-mono text-arkhe-muted uppercase">Tor Circuit</span>
                    <Shield className={`w-3 h-3 ${state.networkInfra.tor.status === 'CONNECTED' ? 'text-arkhe-green' : 'text-blue-400'}`} />
                  </div>
                  <div className="text-xs font-mono font-bold">{state.networkInfra.tor.status}</div>
                  <div className="text-[7px] font-mono text-arkhe-muted mt-1">Latency: {state.networkInfra.tor.latencyMs.toFixed(1)}ms</div>
                </div>
                <div className="bg-black/40 border border-white/5 p-3 rounded">
                  <div className="flex justify-between items-start mb-1">
                    <span className="text-[8px] font-mono text-arkhe-muted uppercase">Message Broker</span>
                    <Server className="w-3 h-3 text-arkhe-green" />
                  </div>
                  <div className="text-xs font-mono font-bold">{state.networkInfra.broker.status}</div>
                  <div className="text-[7px] font-mono text-arkhe-muted mt-1">Processed: {state.networkInfra.broker.messagesProcessed}</div>
                </div>
                <div className="bg-black/40 border border-white/5 p-3 rounded">
                  <div className="flex justify-between items-start mb-1">
                    <span className="text-[8px] font-mono text-arkhe-muted uppercase">Redis Cache</span>
                    <Database className="w-3 h-3 text-arkhe-green" />
                  </div>
                  <div className="text-xs font-mono font-bold">{state.networkInfra.redis.status}</div>
                  <div className="text-[7px] font-mono text-arkhe-muted mt-1">Hits: {state.networkInfra.redis.cacheHits}</div>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4">
              {domains.map((domain: any) => (
                <div key={domain.name} className="bg-white/5 border border-white/10 rounded-lg p-4 flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className={`p-2 rounded bg-black/40 ${domain.health === 'CRITICAL' ? 'text-arkhe-red' : 'text-blue-400'}`}>
                      <Activity className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-xs font-mono font-bold uppercase">{domain.name} Domain</div>
                      <div className="text-[10px] font-mono text-arkhe-muted">Control: {domain.action}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`text-lg font-mono font-bold ${domain.health === 'CRITICAL' ? 'text-arkhe-red' : 'text-blue-400'}`}>
                      {domain.lambda2.toFixed(3)}
                    </div>
                    <div className={`text-[8px] font-mono uppercase ${domain.health === 'CRITICAL' ? 'text-arkhe-red/70' : 'text-arkhe-muted'}`}>
                      {domain.health}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Sidebar Info */}
          <div className="space-y-4">
            <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3 text-blue-400">
                <AlertCircle className="w-4 h-4" />
                <h4 className="text-[10px] font-mono uppercase font-bold text-blue-400">Critical Alerts</h4>
              </div>
              <div className="space-y-2">
                <div className="text-[9px] font-mono text-arkhe-red border-l-2 border-arkhe-red pl-2 py-1 bg-arkhe-red/5">
                  Marketing: Freshness &gt; 5min on campaign_metrics
                </div>
              </div>
            </div>

            <div className="bg-white/5 border border-white/10 rounded-lg p-4 space-y-3">
               <h4 className="text-[10px] font-mono uppercase font-bold text-arkhe-muted">Operational Controls</h4>
               <button
                onClick={() => fetch('/api/sca-data/seed', { method: 'POST' })}
                className="w-full py-2 bg-blue-500 text-black font-mono text-[9px] uppercase font-bold rounded hover:bg-white transition-colors flex items-center justify-center gap-2">
                 <Database className="w-3 h-3" />
                 Holographic Seeding
               </button>
               <button
                onClick={() => fetch('/api/sca-data/ignite', { method: 'POST' })}
                className="w-full py-2 bg-arkhe-green text-black font-mono text-[9px] uppercase font-bold rounded hover:bg-white transition-colors flex items-center justify-center gap-2">
                 <Activity className="w-3 h-3" />
                 Global Ignition
               </button>
               <div className="grid grid-cols-2 gap-2">
                 <button
                  onClick={() => fetch('/api/sca-data/protocol', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ protocol: 'BRAID' }) })}
                  className="py-2 border border-blue-500/30 text-blue-400 font-mono text-[8px] uppercase rounded hover:bg-blue-500/10 transition-colors">
                   Protocol [BRAID]
                 </button>
                 <button
                  onClick={() => fetch('/api/sca-data/protocol', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ protocol: 'COMPUTE' }) })}
                  className="py-2 border border-blue-500/30 text-blue-400 font-mono text-[8px] uppercase rounded hover:bg-blue-500/10 transition-colors">
                   Protocol [COMPUTE]
                 </button>
                 <button
                  onClick={() => fetch('/api/sca-data/protocol', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ protocol: 'HEAL' }) })}
                  className="py-2 border border-arkhe-green/30 text-arkhe-green font-mono text-[8px] uppercase rounded hover:bg-arkhe-green/10 transition-colors">
                   Protocol [HEAL]
                 </button>
                 <button
                  onClick={() => fetch('/api/sca-data/protocol', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ protocol: 'SEAL' }) })}
                  className="py-2 border border-arkhe-green/30 text-arkhe-green font-mono text-[8px] uppercase rounded hover:bg-arkhe-green/10 transition-colors">
                   Protocol [SEAL]
                 </button>
               </div>
               <button className="w-full py-2 border border-white/10 text-arkhe-text font-mono text-[9px] uppercase rounded hover:bg-white/5 transition-colors flex items-center justify-center gap-2">
                 <RefreshCcw className="w-3 h-3" />
                 Trigger Remediation
               </button>
            </div>

            <div className="bg-white/5 border border-white/10 rounded-lg p-4">
              <h4 className="text-[10px] font-mono uppercase font-bold text-blue-400 mb-4">
                Topologia da Malha ASD (N=12)
              </h4>
              <div className="relative h-40 flex items-center justify-center">
                {/* Visualizing the Kagome Lattice */}
                <div className="grid grid-cols-3 gap-2 p-2">
                  {[...Array(12)].map((_, i) => (
                    <motion.div
                      key={i}
                      className="w-4 h-4 border border-blue-500/50 rounded-sm"
                      animate={{
                        opacity: [0.3, 1, 0.3],
                        scale: [1, 1.1, 1],
                        borderColor: ['#3b82f650', '#00d992', '#3b82f650']
                      }}
                      transition={{
                        duration: 2,
                        repeat: Infinity,
                        delay: i * 0.1,
                      }}
                    />
                  ))}
                </div>
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <div className="text-[8px] font-mono text-blue-400 animate-pulse font-bold bg-black/60 px-2">
                    {state.scaData.topologicalState}
                  </div>
                </div>
              </div>
              <div className="mt-4 space-y-1">
                <div className="flex justify-between text-[8px] font-mono">
                  <span>Modo:</span>
                  <span className="text-blue-400 font-bold">{state.scaData.entanglementMode}</span>
                </div>
                <div className="flex justify-between text-[8px] font-mono">
                  <span>R(t) Global:</span>
                  <span className="text-blue-400">{state.scaData.globalOrderR.toFixed(3)}</span>
                </div>
                <div className="flex justify-between text-[8px] font-mono">
                  <span>ATP Cons.:</span>
                  <span className="text-arkhe-green">{state.scaData.atpConsumptionCps} cps</span>
                </div>
                <div className="flex justify-between text-[8px] font-mono">
                  <span>Resiliência:</span>
                  <span className="text-arkhe-green font-bold">TOPOLÓGICA (QSL)</span>
                </div>
              </div>
            </div>

            {state.scaData.protocolLogs.length > 0 && (
              <div className="p-2 bg-black/40 rounded border border-white/5">
                <h4 className="text-[8px] font-mono uppercase text-blue-400 mb-2">Protocol Output: {state.scaData.activeProtocol}</h4>
                <div className="space-y-1 max-h-32 overflow-y-auto custom-scrollbar">
                  {state.scaData.protocolLogs.map((log: any, i: any) => (
                    <div key={i} className="text-[7px] font-mono text-arkhe-muted border-l border-white/10 pl-2 leading-tight">
                      {log}
                    </div>
                  ))}
                </div>
                {state.scaData.lastGateResult && (
                  <div className="mt-2 text-[8px] font-mono text-arkhe-green font-bold">
                    RESULT: {state.scaData.lastGateResult}
                  </div>
                )}
              </div>
            )}

            <div className="p-2">
               <h4 className="text-[8px] font-mono uppercase text-arkhe-muted mb-2">Strategy: Edge-of-Chaos (SBM)</h4>
               <p className="text-[8px] font-mono text-arkhe-muted leading-relaxed">
                 O SCA-Data utiliza o controlador Stabilized by Memory para equilibrar throughput e latência. Circuit-breakers são ativados quando λ₂ cai abaixo de 0.90.
               </p>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
