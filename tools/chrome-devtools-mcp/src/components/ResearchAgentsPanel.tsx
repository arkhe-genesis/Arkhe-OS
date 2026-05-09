
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Search, Database, Zap, Shield, Microscope } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import React, { useState } from 'react';

import type { SimulationState } from '../../server/types';
import { useArkheSimulation } from '../hooks/useArkheSimulation';

interface ResearchModuleProps {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'pending' | 'locked';
  icon: React.ElementType;
}

const ResearchModule = ({ name, description, status, icon: Icon }: ResearchModuleProps) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`p-4 rounded-lg border ${
        status === 'active'
          ? 'bg-arkhe-cyan/5 border-arkhe-cyan/30 text-arkhe-text'
          : status === 'pending'
          ? 'bg-arkhe-muted/5 border-arkhe-muted/20 text-arkhe-muted'
          : 'bg-black/20 border-white/5 text-white/20'
      }`}
    >
      <div className="flex items-center gap-3 mb-2">
        <Icon className={`w-5 h-5 ${status === 'active' ? 'text-arkhe-cyan' : ''}`} />
        <h4 className="font-mono text-sm font-bold uppercase tracking-wider">{name}</h4>
        {status === 'active' && (
          <span className="ml-auto flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-arkhe-cyan opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-arkhe-cyan"></span>
          </span>
        )}
      </div>
      <p className="text-[10px] font-mono leading-relaxed opacity-70">{description}</p>
    </motion.div>
  );
};

export default function ResearchAgentsPanel() {
  const state: SimulationState = useArkheSimulation();
  const [isSearching, setIsSearching] = useState(false);
  const [searchLog, setSearchLog] = useState<string[]>([]);

  const handleSearch = async () => {
    setIsSearching(true);
    setSearchLog(prev => [`> Iniciando consulta ao Banco de Dados de Conhecimento (Akasha)...`, ...prev]);

    // Simulate API calls
    const steps = [
      "Sintonizando receptores de fase Th-229...",
      "Cruzando referências com o Repositório ResearchHub...",
      "Filtrando anomalias via BerryGuard (Opcode 0x214)...",
      "Suturando matrizes de dados ℝ⁴ × ℂ...",
      "Resultados cristalizados. Coerência validada."
    ];

    for (const step of steps) {
      await new Promise(resolve => setTimeout(resolve, 800));
      setSearchLog(prev => [`> ${step}`, ...prev]);
    }

    setIsSearching(false);
  };

  const getStatus = (target: string) => {
    const stages = ['C_PHASE', 'Z_STRUCTURE', 'TZINOROT_EXEC', 'R4_PROJECTION'];
    const currentIdx = stages.indexOf(state.manifestation.stage);
    const targetIdx = stages.indexOf(target);

    if (currentIdx === targetIdx) {return 'active';}
    if (currentIdx > targetIdx) {return 'pending';}
    return 'locked';
  };

  return (
    <div className="bg-[#0a0a0c] border border-[#1f2024] rounded-xl p-6 flex flex-col gap-6 h-full overflow-hidden">
      <div className="flex items-center justify-between border-b border-[#1f2024] pb-4">
        <div className="flex items-center gap-3">
          <Microscope className="w-6 h-6 text-arkhe-cyan" />
          <h2 className="font-mono text-lg font-bold uppercase tracking-[0.2em]">Agentes de Pesquisa</h2>
        </div>
        <button
          onClick={handleSearch}
          disabled={isSearching}
          className={`flex items-center gap-2 px-4 py-2 font-mono text-xs border rounded transition-all ${
            isSearching
              ? 'border-arkhe-cyan/20 text-arkhe-cyan/40 cursor-not-allowed'
              : 'border-arkhe-cyan/50 text-arkhe-cyan hover:bg-arkhe-cyan/10'
          }`}
        >
          <Search className={`w-3 h-3 ${isSearching ? 'animate-spin' : ''}`} />
          {isSearching ? 'PESQUISANDO...' : 'PESQUISAR DADOS'}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <ResearchModule
          id="C_PHASE"
          name="Módulo Fase ℂ"
          description="Processamento de Intencionalidade e Sincronia Bio-Quantum."
          status={getStatus('C_PHASE')}
          icon={Zap}
        />
        <ResearchModule
          id="Z_STRUCTURE"
          name="Módulo Estrutura ℤ"
          description="Arquitetura de Plano Fractal e Coerência Topológica."
          status={getStatus('Z_STRUCTURE')}
          icon={Database}
        />
        <ResearchModule
          id="R4_PROJECTION"
          name="Módulo Projeção ℝ⁴"
          description="Verificação de Manifestação Física e Integridade de Fase."
          status={getStatus('R4_PROJECTION')}
          icon={Shield}
        />
      </div>

      <div className="flex-1 min-h-[120px] bg-black/40 rounded border border-[#1f2024] p-4 font-mono text-[10px] overflow-y-auto">
        <div className="text-arkhe-muted mb-2 uppercase tracking-widest border-b border-white/5 pb-1">Log de Pesquisa</div>
        <AnimatePresence>
          {searchLog.map((log, i) => (
            <motion.div
              key={`${i}-${log}`}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className={`${i === 0 && isSearching ? 'text-arkhe-cyan animate-pulse' : 'text-arkhe-muted'}`}
            >
              {log}
            </motion.div>
          ))}
        </AnimatePresence>
        {searchLog.length === 0 && <div className="text-white/10 italic">Aguardando comando de pesquisa...</div>}
      </div>
    </div>
  );
}
