
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { MapPin, Signal,  Plus } from 'lucide-react';
import React, { useState } from 'react';

import type { SimulationState } from '../../server/types';
import { cn } from '../lib/utils';

import { Card } from './ui/Card';


interface ExpansionPanelProps {
  state: SimulationState;
}

const ExpansionPanel: React.FC<ExpansionPanelProps> = ({ state }) => {
  const [neighborhood, setNeighborhood] = useState('');
  const expansion = state.expansionStatus;

  if (!expansion) {return null;}

  const handleStartExpansion = async () => {
    if (!neighborhood.trim()) {return;}
    try {
      await fetch('/api/expansion/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ targetNeighborhood: neighborhood })
      });
      setNeighborhood('');
    } catch (err) {
      console.error("Failed to start expansion", err);
    }
  };

  return (
    <Card
      title="Expansão Geográfica (Bio-Link 40Hz)"
      icon={<MapPin className="text-arkhe-cyan w-4 h-4" />}
      className="bg-[#0A0E17]/80 border-arkhe-cyan/30"
    >
      <div className="space-y-4">
        <div className="flex justify-between items-center bg-black/40 p-2 rounded border border-white/5">
          <div className="text-[10px] text-white/50 uppercase">Cobertura Populacional</div>
          <div className="text-sm font-bold text-arkhe-cyan font-mono">
            {expansion.totalCoverage?.toLocaleString() || '0'} RESIDENTES
          </div>
        </div>

        <div className="space-y-2">
          {expansion.nodes.map((node) => (
            <div key={node.id} className="flex items-center justify-between p-2 bg-black/20 rounded border border-white/5">
              <div className="flex items-center gap-2">
                <div className={cn(
                  "w-1.5 h-1.5 rounded-full",
                  node.status === 'active' ? 'bg-[#00FFAA]' : 'bg-yellow-500 animate-pulse'
                )} />
                <span className="text-[10px] font-bold text-white/80 uppercase">{node.name}</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1">
                  <Signal className="w-3 h-3 text-white/30" />
                    <span className="text-[9px] text-white/50">{((node.signalStrength || 0) * 100).toFixed(0)}%</span>
                </div>
                <div className="text-[9px] font-mono text-arkhe-cyan">
                    λ₂: {(node.coherence || 0).toFixed(4)}
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="flex gap-2 pt-2 border-t border-white/5">
          <input
            value={neighborhood}
            onChange={(e) => setNeighborhood(e.target.value)}
            placeholder="Novo Bairro (ex: Botafogo)..."
            className="flex-1 h-7 px-2 text-[10px] bg-black/40 border border-white/10 rounded focus:border-arkhe-cyan/50 outline-none text-white font-mono"
          />
          <button
            onClick={handleStartExpansion}
            className="h-7 px-2 flex items-center gap-1 bg-arkhe-cyan/20 hover:bg-arkhe-cyan/30 text-arkhe-cyan border border-arkhe-cyan/30 rounded transition-colors text-[9px] font-mono uppercase"
          >
            <Plus className="w-3 h-3" /> Injetar 40Hz
          </button>
        </div>
      </div>
    </Card>
  );
};

export default ExpansionPanel;
