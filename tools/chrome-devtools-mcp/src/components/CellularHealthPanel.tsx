
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Heart, Activity, Timer, Zap } from 'lucide-react';
import React from 'react';

import type { SimulationState } from '../../server/types';

import { Card } from './ui/Card';


interface CellularHealthPanelProps {
  state: SimulationState;
}

const CellularHealthPanel: React.FC<CellularHealthPanelProps> = ({ state }) => {
  const health = state.cellularHealth;

  if (!health) {return null;}

  const metrics = [
    { label: 'Telômeros', value: `${(health.telomere_length * 100).toFixed(1)}%`, sub: 'Baseline Jovem' },
    { label: 'Estresse Oxid.', value: `${(health.oxidative_stress * 100).toFixed(0)}%`, sub: 'Meta < 30%' },
    { label: 'Efic. Mito.', value: `${(health.mitochondrial_efficiency * 100).toFixed(1)}%`, sub: 'Modo Otimizado' },
    { label: 'Inflamação', value: `${(health.inflammation_marker * 100).toFixed(1)}%`, sub: 'IL-6 / TNF-α' },
  ];

  return (
    <Card
      title="Saúde Celular (Bio-Link 40Hz)"
      icon={<Heart className="text-[#00FFAA] w-4 h-4" />}
      action={
        <div className="flex items-center gap-1 text-[#00FFAA] text-[8px] font-mono">
          <Zap className="w-2 h-2 animate-pulse" />
          ESTÁSIO BIOLÓGICO
        </div>
      }
      className="bg-[#0A0E17]/80 border-[#00FFAA]/30"
    >
      <div className="space-y-4">
        <div className="text-center pb-2 border-b border-white/5">
          <p className="text-[8px] text-white/50 uppercase tracking-widest mb-1">Score Global de Regeneração</p>
          <p className="text-2xl font-bold font-mono text-[#00FFAA]">
            {(health.overall_score * 100).toFixed(1)}
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3">
          {metrics.map((m) => (
            <div key={m.label} className="bg-black/30 p-2 rounded border border-white/5">
              <p className="text-[7px] text-white/40 uppercase mb-1 font-mono tracking-tighter">{m.label}</p>
              <p className="text-xs font-bold text-white/90">{m.value}</p>
              <p className="text-[6px] text-white/30 uppercase italic">{m.sub}</p>
            </div>
          ))}
        </div>

        <div className="flex justify-between items-center text-[7px] uppercase font-mono text-white/20">
          <div className="flex items-center gap-1">
            <Activity className="w-2 h-2" />
            Taxa: {health.regeneration_rate.toFixed(3)} cells/h
          </div>
          <div className="flex items-center gap-1">
            <Timer className="w-2 h-2" />
            24h Projection
          </div>
        </div>
      </div>
    </Card>
  );
};

export default CellularHealthPanel;
