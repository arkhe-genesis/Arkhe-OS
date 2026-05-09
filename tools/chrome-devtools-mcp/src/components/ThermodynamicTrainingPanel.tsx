
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Zap, Activity, Play } from 'lucide-react';
import React from 'react';

import type { ThermodynamicTrainingReport } from '../../server/types';

import { Card } from './ui/Card';

interface ThermodynamicTrainingPanelProps {
  report?: ThermodynamicTrainingReport;
  onRunTraining: () => void;
}

const ThermodynamicTrainingPanel: React.FC<ThermodynamicTrainingPanelProps> = ({ report, onRunTraining }) => {
  if (!report) {return null;}

  return (
    <Card
      title="THERMODYNAMIC HARDWARE TRAINING"
      icon={<Zap className="w-4 h-4 text-yellow-400" />}
      className="font-mono"
    >
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-2 text-[10px]">
          <div className="space-y-1">
            <p className="text-arkhe-muted uppercase">Method</p>
            <p className="text-white">{report.method}</p>
          </div>
          <div className="space-y-1 text-right">
            <p className="text-arkhe-muted uppercase">Oscillators</p>
            <p className="text-arkhe-cyan">{(report.parameters as { n_oscillators?: number }).n_oscillators}</p>
          </div>
        </div>

        <div className="p-3 bg-yellow-500/5 border border-yellow-500/20 rounded">
          <div className="flex justify-between items-center mb-2">
            <span className="text-[10px] text-arkhe-muted uppercase font-bold flex items-center gap-1">
              <Activity className="w-3 h-3 text-yellow-400" />
              Action Loss (Onsager-Machlup)
            </span>
            <span className="text-[10px] text-yellow-400 font-bold">
              {(report.parameters as { final_loss?: number }).final_loss?.toFixed(6)}
            </span>
          </div>
          <div className="h-1.5 w-full bg-yellow-500/10 rounded-full overflow-hidden">
             <div
               className="h-full bg-yellow-500 transition-all duration-1000"
               style={{ width: `${Math.max(10, 100 - ((report.parameters as { final_loss?: number }).final_loss || 0) * 20)}%` }}
             />
          </div>
        </div>

        <button
          onClick={onRunTraining}
          className="w-full flex items-center justify-center gap-2 py-2 bg-yellow-600/20 border border-yellow-500/40 hover:bg-yellow-600/30 transition-colors text-yellow-300 text-[10px] font-bold text-white"
        >
          <Play className="w-3 h-3" />
          START ANALOG SYNTHESIS
        </button>

        <p className="text-[9px] text-arkhe-muted italic text-center">
          Status: {report.status}
        </p>
      </div>
    </Card>
  );
};

export default ThermodynamicTrainingPanel;
