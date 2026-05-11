
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Shield, Code, BarChart, Globe, Lock, Brain, Network, X } from 'lucide-react';
import { motion } from 'motion/react';
import React from 'react';

import type { EnterpriseSubagentState } from '../../server/types';
import type { SimulationState } from '../../server/types';
import { useArkheSimulation } from '../hooks/useArkheSimulation';

interface DomainSectionProps {
  title: string;
  icon: React.ReactNode;
  agents: EnterpriseSubagentState[];
  color: string;
}

const DomainSection: React.FC<DomainSectionProps> = ({ title, icon, agents, color }) => {
  const [loading, setLoading] = React.useState<string | null>(null);

  const triggerAction = async (agentId: string) => {
    setLoading(agentId);
    try {
      let action = 'process';
      let body: unknown = {};

      if (agentId === 'G1') {
        action = 'validate-policy';
        body = { policy: 'Permission: allow data extraction for POC' };
      } else if (agentId === 'D1') {
        action = 'deploy-circuit';
      } else if (agentId === 'X1') {
        action = 'translate';
        body = { source_data: { user: 'operator-zero', action: 'login' } };
      }

      await fetch(`/api/subagent/${agentId}/${action}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Kuramoto-Phase': '1.57',
          'X-ZK-Proof': '0x' + Math.random().toString(16).slice(2, 34)
        },
        body: JSON.stringify(body)
      });
    } catch (error) {
      console.error(`Failed to trigger action for ${agentId}:`, error);
    } finally {
      setTimeout(() => setLoading(null), 1000);
    }
  };

  const isPOCAgent = (id: string) => ['G1', 'D1', 'X1'].includes(id);

  return (
    <div className="bg-[#1a1b1e] border border-[#2a2b30] rounded-lg p-4 overflow-hidden">
      <div className="flex items-center gap-2 mb-4 border-b border-[#2a2b30] pb-2">
        <div className={`${color}`}>{icon}</div>
        <h3 className="text-sm font-bold text-white uppercase tracking-widest">{title}</h3>
      </div>
      <div className="space-y-3">
        {agents.map((agent) => (
          <div key={agent.id} className="bg-black/30 border border-[#2a2b30] rounded p-2 text-[10px] font-mono">
            <div className="flex justify-between items-start mb-1">
              <span className="text-arkhe-cyan">{agent.id}: {agent.name}</span>
              <span className={`px-1.5 py-0.5 rounded border border-current ${
                agent.status === 'alert' ? 'text-red-400' :
                agent.status === 'active' ? 'text-emerald-400' : 'text-amber-400'
              }`}>
                {agent.status.toUpperCase()}
              </span>
            </div>
            <div className="text-white/70 mb-1 leading-tight">{agent.function}</div>
            <div className="text-white/40 italic mb-2">Theory: {agent.theory}</div>
            <div className="flex justify-between items-center text-[9px] border-t border-[#2a2b30] pt-1 mb-2">
              <div className="flex flex-col gap-0.5">
                <span className="text-emerald-500/70 uppercase tracking-tighter">Metric: {agent.metric}</span>
                {agent.status === 'active' && (
                  <span className="text-arkhe-cyan/60 text-[7px] uppercase font-bold">
                    [ZK-PROOF: VERIFICADO]
                  </span>
                )}
              </div>
              <span className="text-white/30 truncate max-w-[120px]" title={agent.lastAction}>
                {agent.lastAction}
              </span>
            </div>
            {isPOCAgent(agent.id) && (
              <button
                onClick={() => triggerAction(agent.id)}
                disabled={loading === agent.id}
                className={`w-full py-1.5 rounded border transition-all uppercase tracking-tighter text-[9px] font-bold ${
                  loading === agent.id
                    ? 'bg-arkhe-cyan/20 border-arkhe-cyan text-arkhe-cyan animate-pulse'
                    : 'bg-black/40 border-arkhe-cyan/50 text-arkhe-cyan hover:bg-arkhe-cyan hover:text-black'
                }`}
              >
                {loading === agent.id ? 'EXECUTANDO qhttp COLLAPSE...' : `ACIONAR ${agent.name} POC`}
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

interface EnterprisePlusPanelProps {
  onClose: () => void;
}

export const EnterprisePlusPanel: React.FC<EnterprisePlusPanelProps> = ({ onClose }) => {
  const state: any = useArkheSimulation();
  const enterprise = state.enterpriseSubagents;

  if (!enterprise) {return null;}

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 md:p-8">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-[#111214] border border-arkhe-border rounded-xl w-full max-w-7xl h-[90vh] flex flex-col shadow-2xl overflow-hidden relative"
      >
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-arkhe-muted hover:text-white transition-colors z-10"
        >
          <X className="w-6 h-6" />
        </button>

        <div className="p-6 border-b border-arkhe-border flex items-center justify-between bg-black/40">
          <div className="flex items-center space-x-3">
            <Globe className="w-6 h-6 text-arkhe-cyan" />
            <div>
              <h2 className="text-xl font-bold text-white tracking-widest uppercase">Arkhe(n) Enterprise Plus</h2>
              <p className="text-[10px] text-arkhe-muted font-mono uppercase tracking-[0.2em]">Interoperabilidade de Cidadelas Corporativas</p>
            </div>
          </div>
          <div className="flex items-center gap-6">
            <div className="text-right">
              <div className="text-[10px] text-arkhe-muted uppercase font-mono">Global Coherence</div>
              <div className="text-lg font-mono text-emerald-400">R(t) = {state.currentLambda.toFixed(4)}</div>
            </div>
            <div className="text-right">
              <div className="text-[10px] text-arkhe-muted uppercase font-mono">qhttp Backbone</div>
              <div className="text-lg font-mono text-cyan-400">PQ-TLS 1.3</div>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6 bg-black/20 custom-scrollbar">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <DomainSection
              title="Governança & Compliance"
              icon={<Shield className="w-5 h-5" />}
              agents={enterprise.governance}
              color="text-amber-400"
            />
            <DomainSection
              title="Desenvolvimento & DevOps"
              icon={<Code className="w-5 h-5" />}
              agents={enterprise.devops}
              color="text-cyan-400"
            />
            <DomainSection
              title="Segurança & Privacidade"
              icon={<Lock className="w-5 h-5" />}
              agents={enterprise.security}
              color="text-red-400"
            />
            <DomainSection
              title="IA & AGI (Mesh-LLM)"
              icon={<Brain className="w-5 h-5" />}
              agents={enterprise.ia}
              color="text-purple-400"
            />
            <DomainSection
              title="Operações & Finanças"
              icon={<BarChart className="w-5 h-5" />}
              agents={enterprise.operations}
              color="text-emerald-400"
            />
            <DomainSection
              title="Interoperabilidade"
              icon={<Network className="w-5 h-5" />}
              agents={enterprise.interoperability}
              color="text-blue-400"
            />
          </div>
        </div>

        <div className="p-4 bg-black/60 border-t border-arkhe-border flex justify-between items-center text-[10px] font-mono">
          <div className="flex gap-4">
            <span className="text-arkhe-muted">PROTOCOL: <span className="text-white">qhttp/2.0</span></span>
            <span className="text-arkhe-muted">CONSENSUS: <span className="text-white">MuSig2/FROST</span></span>
            <span className="text-arkhe-muted">ONTOLOGY: <span className="text-white">BFO/DOLCE</span></span>
          </div>
          <div className="text-arkhe-cyan animate-pulse">
            SISTEMA OPERACIONAL DA CIDADELA REESCRITO EM TEMPO REAL...
          </div>
        </div>
      </motion.div>
    </div>
  );
};
export default EnterprisePlusPanel;
