
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Layers, Activity, Search, Target } from 'lucide-react';
import React from 'react';

import type { LayerSweepReport } from '../../server/types';

import { Card } from './ui/Card';

interface LayerSweepPanelProps {
  report?: LayerSweepReport;
  onRunSweep: () => void;
}

const LayerSweepPanel: React.FC<LayerSweepPanelProps> = ({ report, onRunSweep }) => {
  if (!report) {return null;}

  // Simple visualization without recharts for robustness if needed,
  // but I'll stick to the UI design
  return (
    <Card
      title="LAYER-SWEEP ANALYSIS"
      icon={<Layers className="w-4 h-4 text-emerald-400" />}
      className="font-mono"
    >
      <div className="space-y-4">
        <div className="flex justify-between items-center text-[10px]">
          <span className="text-arkhe-muted">STABLE LAYER</span>
          <span className="text-emerald-400 font-bold">L{report.best_layer}</span>
        </div>

        <div className="h-24 flex items-end gap-0.5 border-b border-arkhe-border pb-1">
          {report.coct_sweep.map((l, i) => (
            <div
              key={i}
              className="bg-emerald-500/40 hover:bg-emerald-500 transition-colors flex-1"
              style={{ height: `${l.lambda2 * 100}%` }}
              title={`Layer ${l.layer}: λ₂=${l.lambda2.toFixed(4)}`}
            />
          ))}
        </div>

        <div className="grid grid-cols-2 gap-2 text-[10px]">
          <div className="p-2 bg-emerald-500/5 border border-emerald-500/20 rounded flex items-center gap-2">
            <Target className="w-3 h-3 text-emerald-400" />
            <div>
              <p className="text-arkhe-muted uppercase">Stable Layer</p>
              <p className="text-emerald-400 font-bold">Layer {report.best_layer}</p>
            </div>
          </div>
          <div className="p-2 bg-emerald-500/5 border border-emerald-500/20 rounded flex items-center gap-2">
            <Activity className="w-3 h-3 text-emerald-400" />
            <div>
              <p className="text-arkhe-muted uppercase">Max λ₂</p>
              <p className="text-emerald-400 font-bold">{report.max_lambda2.toFixed(4)}</p>
            </div>
          </div>
        </div>

        <button
          onClick={onRunSweep}
          className="w-full flex items-center justify-center gap-2 py-2 bg-emerald-600/20 border border-emerald-500/40 hover:bg-emerald-600/30 transition-colors text-emerald-300 text-[10px] font-bold text-white"
        >
          <Search className="w-3 h-3" />
          EXECUTE LAYER-SWEEP
        </button>

        <p className="text-[9px] text-arkhe-muted italic text-center">
          {report.summary}
        </p>
      </div>
    </Card>
  );
};

export default LayerSweepPanel;
