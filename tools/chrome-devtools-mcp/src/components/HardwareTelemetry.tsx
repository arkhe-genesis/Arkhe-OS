
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Cpu, Zap, Activity } from 'lucide-react';

import { Card } from './ui/Card';


interface HardwareTelemetryProps {
  hardware: {
    fpgaUtilization: number;
    segPower: number;
    tmrFaultsCorrected: number;
    bramScrubbingActive: boolean;
  };
}

export default function HardwareTelemetry({ hardware }: HardwareTelemetryProps) {
  return (
    <Card
      title="Hardware Telemetry"
      icon={<Cpu className="w-4 h-4" />}
      status={hardware.fpgaUtilization > 80 ? 'warning' : 'normal'}
    >
      <div className="flex flex-col gap-4">
        {/* FPGA Utilization */}
        <div className="bg-[#151619] border border-arkhe-border rounded p-3">
          <div className="flex justify-between items-center mb-2">
            <div className="flex items-center gap-2">
              <Activity className="w-3 h-3 text-arkhe-muted" />
              <span className="text-[10px] font-mono text-arkhe-muted uppercase">FPGA Utilization</span>
            </div>
            <span className={`text-[10px] font-mono font-bold ${hardware.fpgaUtilization > 80 ? 'text-arkhe-orange' : 'text-arkhe-cyan'}`}>
              {hardware.fpgaUtilization.toFixed(1)}%
            </span>
          </div>
          <div className="h-1.5 w-full bg-black/40 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-300 ${hardware.fpgaUtilization > 80 ? 'bg-arkhe-orange' : 'bg-arkhe-cyan'}`}
              style={{ width: `${Math.min(100, hardware.fpgaUtilization)}%` }}
            />
          </div>
        </div>

        {/* SEG Power */}
        <div className="bg-[#151619] border border-arkhe-border rounded p-3">
          <div className="flex justify-between items-center mb-2">
            <div className="flex items-center gap-2">
              <Zap className="w-3 h-3 text-arkhe-muted" />
              <span className="text-[10px] font-mono text-arkhe-muted uppercase">SEG Power Draw</span>
            </div>
            <span className="text-[10px] font-mono font-bold text-arkhe-text">
              {hardware.segPower.toFixed(1)} W
            </span>
          </div>
          <div className="h-1.5 w-full bg-black/40 rounded-full overflow-hidden">
            <div
              className="h-full bg-arkhe-text transition-all duration-300"
              style={{ width: `${Math.min(100, (hardware.segPower / 350) * 100)}%` }}
            />
          </div>
        </div>
      </div>
    </Card>
  );
}
