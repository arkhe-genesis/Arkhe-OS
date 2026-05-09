
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Brain, Network, GitMerge, Box,  CheckCircle2 } from 'lucide-react';
import { motion } from 'motion/react';
import React from 'react';

interface ManifestationCycleProps {
  manifestation: {
    stage: 'C_PHASE' | 'Z_STRUCTURE' | 'TZINOROT_EXEC' | 'R4_PROJECTION';
    activeTask: string;
    retrocausalIntegrity: number;
    invariantsVerified: number;
  };
}

export default function ManifestationCycle({ manifestation }: ManifestationCycleProps) {
  const stages = [
    { id: 'C_PHASE', label: 'Fase ℂ', desc: 'Intenção', icon: Brain },
    { id: 'Z_STRUCTURE', label: 'Estrutura ℤ', desc: 'Plano Fractal', icon: Network },
    { id: 'TZINOROT_EXEC', label: 'Tzinorot', desc: 'TDD Retrocausal', icon: GitMerge },
    { id: 'R4_PROJECTION', label: 'Projeção ℝ⁴', desc: 'Verificação', icon: Box },
  ];

  const currentIndex = stages.findIndex(s => s.id === manifestation.stage);

  return (
    <div className="bg-black/40 border border-arkhe-border/50 rounded-xl p-4 flex flex-col h-full">
      <div className="flex items-center justify-between mb-8">
        <h2 className="text-xs font-mono text-arkhe-cyan uppercase tracking-wider flex items-center gap-2">
          <GitMerge className="w-4 h-4" />
          Manifestation Pipeline
        </h2>
        <div className="flex flex-col items-end gap-1 text-[10px] font-mono">
          <div className="flex items-center gap-1 text-arkhe-green">
            <CheckCircle2 className="w-3 h-3" />
            {manifestation.invariantsVerified} Invariantes
          </div>
          <div className="flex items-center gap-1 text-arkhe-cyan">
            Integridade: {manifestation.retrocausalIntegrity}%
          </div>
        </div>
      </div>

      <div className="flex-1 flex flex-col justify-center relative px-4">
        {/* Connecting Line */}
        <div className="absolute top-5 left-8 right-8 h-[1px] bg-arkhe-border/30 z-0" />

        <div className="flex items-start justify-between relative z-10">
          {stages.map((stage, idx) => {
            const Icon = stage.icon;
            const isActive = idx === currentIndex;
            const isPast = idx < currentIndex;

            return (
              <div key={stage.id} className="flex flex-col items-center gap-3 w-16">
                <motion.div
                  animate={{
                    scale: isActive ? 1.1 : 1,
                    borderColor: isActive ? '#00f0ff' : isPast ? '#00ff9d' : '#333',
                    backgroundColor: isActive ? 'rgba(0, 240, 255, 0.1)' : 'rgba(0,0,0,0.8)'
                  }}
                  className={`w-10 h-10 rounded-full border-2 flex items-center justify-center transition-colors duration-500 bg-black`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-arkhe-cyan' : isPast ? 'text-arkhe-green' : 'text-arkhe-muted'}`} />
                </motion.div>
                <div className="text-center w-full">
                  <div className={`text-[9px] font-mono font-bold leading-tight mb-1 ${isActive ? 'text-arkhe-cyan' : isPast ? 'text-arkhe-green' : 'text-arkhe-muted'}`}>
                    {stage.label}
                  </div>
                  <div className="text-[8px] font-mono text-arkhe-muted/70 leading-tight">
                    {stage.desc}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="mt-6 bg-[#1f2024]/50 border border-arkhe-border/30 rounded p-3 flex items-center gap-3">
        <div className="w-2 h-2 rounded-full bg-arkhe-cyan animate-pulse shrink-0" />
        <div className="text-[10px] font-mono text-arkhe-text truncate">
          <span className="text-arkhe-muted mr-2">TAREFA ATIVA:</span>
          {manifestation.activeTask}
        </div>
      </div>
    </div>
  );
}
