
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Activity } from 'lucide-react';

import { Card } from './ui/Card';


interface ThermodynamicsPanelProps {
  thermo: {
    coherenceC: number;
    dissipationF: number;
    d2: number;
    d3: number;
  };
}

export default function ThermodynamicsPanel({ thermo }: ThermodynamicsPanelProps) {
  const cPercent = Math.min(100, Math.max(0, thermo.coherenceC * 100));
  const fPercent = Math.min(100, Math.max(0, thermo.dissipationF * 100));

  return (
    <Card
      title="Non-Extensive Thermodynamics"
      icon={<Activity className="w-4 h-4" />}
      status="normal"
    >
      <div className="flex flex-col gap-4">
        {/* C + F = 1 Equation Visualizer */}
        <div className="bg-[#151619] border border-arkhe-border rounded p-3">
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs font-mono text-arkhe-muted uppercase">Conservation Law</span>
            <span className="text-xs font-mono font-bold text-arkhe-text">C + F = 1</span>
          </div>

          <div className="h-4 w-full flex rounded-sm overflow-hidden border border-black/20">
            <div
              className="bg-arkhe-cyan transition-all duration-300 flex items-center justify-center"
              style={{ width: `${cPercent}%` }}
            >
              {cPercent > 15 && <span className="text-[8px] font-mono font-bold text-black">C</span>}
            </div>
            <div
              className="bg-arkhe-red transition-all duration-300 flex items-center justify-center"
              style={{ width: `${fPercent}%` }}
            >
              {fPercent > 15 && <span className="text-[8px] font-mono font-bold text-black">F</span>}
            </div>
          </div>

          <div className="flex justify-between mt-1 text-[10px] font-mono">
            <span className="text-arkhe-cyan">Coherence: {thermo.coherenceC.toFixed(3)}</span>
            <span className="text-arkhe-red">Dissipation: {thermo.dissipationF.toFixed(3)}</span>
          </div>
        </div>

        {/* Universal Dissipation */}
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-[#151619] border border-arkhe-border rounded p-3">
            <div className="text-[10px] font-mono text-arkhe-muted uppercase mb-1">D₂ (2-Body)</div>
            <div className="text-xs font-mono font-bold text-arkhe-text mb-1">~ k⁻³</div>
            <div className="text-[10px] font-mono text-arkhe-orange">{thermo.d2.toExponential(2)}</div>
          </div>
          <div className="bg-[#151619] border border-arkhe-border rounded p-3">
            <div className="text-[10px] font-mono text-arkhe-muted uppercase mb-1">D₃ (3-Body)</div>
            <div className="text-xs font-mono font-bold text-arkhe-text mb-1">~ k⁻⁴</div>
            <div className="text-[10px] font-mono text-arkhe-orange">{thermo.d3.toExponential(2)}</div>
          </div>
        </div>
      </div>
    </Card>
  );
}
