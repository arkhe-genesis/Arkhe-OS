
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import {  TrendingDown, Bell, ShieldAlert } from 'lucide-react';
import React from 'react';

import type { SimulationState } from '../../server/types';
import { cn } from '../lib/utils';

import { Card } from './ui/Card';


interface ForecasterPanelProps {
  state: SimulationState;
}

const ForecasterPanel: React.FC<ForecasterPanelProps> = ({ state }) => {
  const forecaster = state.forecaster;

  if (!forecaster) {return null;}

  return (
    <Card
      title="Bio-Quantum Forecaster"
      icon={<TrendingDown className="text-[#FF5A1A] w-4 h-4" />}
      action={
        <div className={cn(
          "px-2 py-0.5 rounded text-[8px] border",
          forecaster.probability > 0.7 ? 'bg-red-500/10 text-red-400 border-red-500/30 animate-pulse' : 'bg-[#00FFAA]/10 text-[#00FFAA] border-[#00FFAA]/30'
        )}>
          {forecaster.probability > 0.7 ? 'CRITICAL RISK' : 'STABLE'}
        </div>
      }
      className="bg-[#0A0E17]/80 border-[#FF5A1A]/30"
    >
      <div className="space-y-3">
        <div className="flex justify-between items-end">
          <div>
            <p className="text-[8px] text-white/50 uppercase tracking-tighter">Risco de Colapso (5m)</p>
            <p className={cn(
              "text-xl font-bold font-mono",
              forecaster.probability > 0.7 ? 'text-red-500' : 'text-[#00FFAA]'
            )}>
              {(forecaster.probability * 100).toFixed(1)}%
            </p>
          </div>
          <div className="text-right">
            <p className="text-[8px] text-white/50 uppercase tracking-tighter">λ₂ Projetado</p>
            <p className="text-sm font-bold font-mono text-white/80">
              {forecaster.predictedLambda.toFixed(4)}
            </p>
          </div>
        </div>

        {forecaster.probability > 0.7 && (
          <div className="p-2 bg-red-500/10 border border-red-500/30 rounded flex items-start gap-2 animate-pulse">
            <ShieldAlert className="w-4 h-4 text-red-500 shrink-0" />
            <p className="text-[10px] text-red-400 leading-tight">
              Instabilidade biológica detectada. Bio-Link intensificando pulso de 40Hz para amortecer queda.
            </p>
          </div>
        )}

        <div className="flex items-center gap-2 text-[8px] text-white/30 uppercase font-mono">
          <Bell className="w-3 h-3" />
          Alertas Emitidos: {forecaster.alertsIssued}
        </div>
      </div>
    </Card>
  );
};

export default ForecasterPanel;
