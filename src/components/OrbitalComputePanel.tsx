
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Satellite,  Layers, Radio } from 'lucide-react';
import React from 'react';

export interface OrbitalState {
  nodeName: string;
  altitudeKm: number;
  telemetryLatencyMs: number;
  computeLoad: number;
  radiationFlux: number;
  osStack: {
    execution: string;
    control: string;
    simulation: string;
    compute: string;
  };
}

export default function OrbitalComputePanel({ orbital }: { orbital: OrbitalState }) {
  return (
    <div className="bg-[#111214] border border-arkhe-border rounded-xl p-4 flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Satellite className="w-5 h-5 text-arkhe-cyan" />
          <h2 className="text-sm font-bold uppercase tracking-widest text-arkhe-cyan">Orbital Compute Uplink</h2>
        </div>
        <div className="flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-arkhe-green opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-arkhe-green"></span>
          </span>
          <span className="text-xs font-mono text-arkhe-green">LINK ACTIVE</span>
        </div>
      </div>

      <div className="bg-black/40 p-3 rounded-lg border border-arkhe-border/50 mb-4">
        <div className="flex justify-between items-center mb-2">
          <div className="text-xs font-mono text-arkhe-muted uppercase">Target Node</div>
          <div className="text-xs font-mono text-arkhe-text font-bold">{orbital.nodeName}</div>
        </div>
        <div className="grid grid-cols-3 gap-2 mt-3">
          <div className="flex flex-col">
            <span className="text-[10px] font-mono text-arkhe-muted uppercase">Altitude</span>
            <span className="text-sm font-mono text-arkhe-cyan">{orbital.altitudeKm.toFixed(1)} km</span>
          </div>
          <div className="flex flex-col">
            <span className="text-[10px] font-mono text-arkhe-muted uppercase">Latency</span>
            <span className="text-sm font-mono text-arkhe-orange">{orbital.telemetryLatencyMs.toFixed(0)} ms</span>
          </div>
          <div className="flex flex-col">
            <span className="text-[10px] font-mono text-arkhe-muted uppercase">Load</span>
            <span className="text-sm font-mono text-arkhe-green">{orbital.computeLoad.toFixed(1)}%</span>
          </div>
        </div>
      </div>

      <div className="flex-1 flex flex-col gap-2">
        <h3 className="text-[10px] font-mono text-arkhe-muted uppercase mb-1 flex items-center gap-1">
          <Layers className="w-3 h-3" /> Physical world-os Stack
        </h3>

        <div className="grid grid-cols-1 gap-2">
          <div className="flex items-center justify-between bg-[#1f2024]/50 p-2 rounded border border-arkhe-border/30">
            <span className="text-xs font-mono text-arkhe-muted w-24">Compute</span>
            <span className="text-xs font-mono text-arkhe-cyan flex-1 text-right">{orbital.osStack.compute}</span>
          </div>
          <div className="flex items-center justify-between bg-[#1f2024]/50 p-2 rounded border border-arkhe-border/30">
            <span className="text-xs font-mono text-arkhe-muted w-24">Simulation</span>
            <span className="text-xs font-mono text-arkhe-cyan flex-1 text-right">{orbital.osStack.simulation}</span>
          </div>
          <div className="flex items-center justify-between bg-[#1f2024]/50 p-2 rounded border border-arkhe-border/30">
            <span className="text-xs font-mono text-arkhe-muted w-24">Control</span>
            <span className="text-xs font-mono text-arkhe-cyan flex-1 text-right">{orbital.osStack.control}</span>
          </div>
          <div className="flex items-center justify-between bg-[#1f2024]/50 p-2 rounded border border-arkhe-border/30">
            <span className="text-xs font-mono text-arkhe-muted w-24">Execution</span>
            <span className="text-xs font-mono text-arkhe-cyan flex-1 text-right">{orbital.osStack.execution}</span>
          </div>
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-arkhe-border/50 flex justify-between items-center">
        <div className="flex items-center gap-1 text-[10px] font-mono text-arkhe-muted">
          <Radio className="w-3 h-3" />
          <span>RAD FLUX: {orbital.radiationFlux.toFixed(2)} µSv/h</span>
        </div>
        <div className="text-[10px] font-mono text-arkhe-muted">
          ORBVM OFF-PLANET EXTENSION
        </div>
      </div>
    </div>
  );
}
