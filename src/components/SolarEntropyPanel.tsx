
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Sun, TrendingDown, TrendingUp, Info } from 'lucide-react';
import React from 'react';

import type { SolarEntropyReport } from '../../server/types';

import { Card } from './ui/Card';

interface SolarEntropyPanelProps {
  report?: SolarEntropyReport;
  onRunAnalysis: () => void;
}

const SolarEntropyPanel: React.FC<SolarEntropyPanelProps> = ({ report, onRunAnalysis }) => {
  if (!report) {return null;}

  return (
    <Card
      title="HELIO-LISTEN: INFODYNAMICS"
      icon={<Sun className="w-4 h-4 text-orange-400" />}
      className="font-mono"
    >
      <div className="space-y-4">
        <div className="flex justify-between items-center text-[10px]">
          <span className="text-arkhe-muted">ENTROPY SLOPE (dS/dt)</span>
          <span className={`font-bold flex items-center gap-1 ${report.slope < 0 ? 'text-emerald-400' : 'text-red-400'}`}>
            {report.slope < 0 ? <TrendingDown className="w-3 h-3" /> : <TrendingUp className="w-3 h-3" />}
            {report.slope.toFixed(6)} bits/yr
          </span>
        </div>

        <div className="p-3 bg-arkhe-cyan/5 border border-arkhe-cyan/10 rounded">
          <p className="text-[10px] text-arkhe-muted mb-2 uppercase font-bold flex items-center gap-2">
            <Info className="w-3 h-3" />
            Vopson's 2nd Law
          </p>
          <div className="flex justify-between items-center">
             <span className="text-[10px] text-white">Validation Status:</span>
             <span className={`text-[10px] font-bold ${report.confirmed ? 'text-emerald-400' : 'text-arkhe-muted'}`}>
               {report.confirmed ? '✅ CONFIRMED' : 'WAITING FOR DATA'}
             </span>
          </div>
          <p className="text-[8px] text-arkhe-muted mt-2 leading-relaxed">
            The Solar system exhibits information self-compression.
            Information is conserved as magnetic phase coherence.
          </p>
        </div>

        <button
          onClick={onRunAnalysis}
          className="w-full flex items-center justify-center gap-2 py-2 bg-orange-600/20 border border-orange-500/40 hover:bg-orange-600/30 transition-colors text-orange-300 text-[10px] font-bold text-white"
        >
          ANALYZE REAL SILSO DATA
        </button>
      </div>
    </Card>
  );
};

export default SolarEntropyPanel;
