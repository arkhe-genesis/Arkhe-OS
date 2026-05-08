
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Activity, Gauge, ShieldCheck, Zap, Info, Binary } from 'lucide-react';
import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

import type { SimulationState } from '../../server/types';
import { useArkheSimulation } from '../hooks/useArkheSimulation';

interface CHSHMonitorPanelProps {
  onClose: () => void;
}

export default function CHSHMonitorPanel({ onClose }: CHSHMonitorPanelProps) {
  const state = useArkheSimulation();
  const chsh = state.chshMonitor as any;
  const state: SimulationState = useArkheSimulation();
  const chsh = state.chshMonitor;

  if (!chsh) {return null;}

  return (
    <div className="bg-black/90 border border-arkhe-cyan/30 rounded-xl overflow-hidden flex flex-col max-h-[90vh] w-full max-w-5xl shadow-[0_0_30px_rgba(0,255,170,0.1)] backdrop-blur-md">
      <div className="px-6 py-4 border-b border-arkhe-cyan/20 flex items-center justify-between bg-arkhe-cyan/5">
        <div className="flex items-center gap-3">
          <Gauge className="w-5 h-5 text-arkhe-cyan animate-pulse" />
          <div>
            <h2 className="text-sm font-bold font-mono uppercase tracking-[0.2em] text-arkhe-cyan">
              CHSH Realtime Monitor
            </h2>
            <p className="text-[10px] font-mono text-arkhe-muted uppercase">
              Protocol: CHSH_REALTIME_MONITOR // Block: {chsh.arkheChainBlock}
            </p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="text-arkhe-muted hover:text-white font-mono text-xs transition-colors px-2 py-1 border border-arkhe-border rounded hover:border-arkhe-cyan/50"
        >
          [X] CLOSE_TERMINAL
        </button>
      </div>

      <div className="p-6 overflow-y-auto space-y-6">
        {/* Live Telemetry Header */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-zinc-900/50 border border-arkhe-border p-4 rounded-lg">
            <div className="text-[10px] font-mono text-arkhe-muted uppercase mb-1">Status</div>
            <div className="text-xs font-bold font-mono text-arkhe-cyan flex items-center gap-2">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-arkhe-cyan opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-arkhe-cyan"></span>
              </span>
              {chsh.liveTelemetry.status}
            </div>
          </div>
          <div className="bg-zinc-900/50 border border-arkhe-border p-4 rounded-lg">
            <div className="text-[10px] font-mono text-arkhe-muted uppercase mb-1">S-Value (Bell Violation)</div>
            <div className={`text-xl font-bold font-mono ${chsh.liveTelemetry.currentS && chsh.liveTelemetry.currentS > 2.8 ? 'text-arkhe-green' : 'text-arkhe-cyan'}`}>
              {chsh.liveTelemetry.currentS?.toFixed(4) || '---'}
            </div>
          </div>
          <div className="bg-zinc-900/50 border border-arkhe-border p-4 rounded-lg">
            <div className="text-[10px] font-mono text-arkhe-muted uppercase mb-1">Data Points</div>
            <div className="text-xl font-bold font-mono text-white">
              {chsh.liveTelemetry.dataPoints}
            </div>
          </div>
          <div className="bg-zinc-900/50 border border-arkhe-border p-4 rounded-lg">
            <div className="text-[10px] font-mono text-arkhe-muted uppercase mb-1">Stability</div>
            <div className="text-xs font-bold font-mono text-arkhe-cyan uppercase tracking-wider">
              {chsh.liveTelemetry.stabilityIndicator}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Chart */}
          <div className="lg:col-span-2 bg-zinc-900/30 border border-arkhe-border rounded-xl p-4 h-[300px]">
             <div className="flex items-center justify-between mb-4">
               <h3 className="text-[10px] font-mono text-arkhe-muted uppercase tracking-widest flex items-center gap-2">
                 <Activity className="w-3 h-3" /> Live S-Value Trajectory
               </h3>
               <div className="text-[10px] font-mono text-arkhe-muted">
                 Target: {chsh.expectedOutcomes.targetEntanglement}
               </div>
             </div>
             <ResponsiveContainer width="100%" height="100%">
               <LineChart data={chsh.liveTelemetry.history}>
                 <CartesianGrid strokeDasharray="3 3" stroke="#1f2024" vertical={false} />
                 <XAxis
                   dataKey="time"
                   stroke="#4b4c52"
                   fontSize={10}
                   tickLine={false}
                   axisLine={false}
                 />
                 <YAxis
                   stroke="#4b4c52"
                   fontSize={10}
                   tickLine={false}
                   axisLine={false}
                   domain={[1.8, 3.0]}
                 />
                 <Tooltip
                   contentStyle={{ backgroundColor: '#0a0a0c', border: '1px solid #1f2024', borderRadius: '4px', fontSize: '10px' }}
                   itemStyle={{ color: '#00ffaa' }}
                 />
                 <ReferenceLine y={2.0} label={{ position: 'right', value: 'Classical', fill: '#4b4c52', fontSize: 8 }} stroke="#4b4c52" strokeDasharray="3 3" />
                 <ReferenceLine y={2.8} label={{ position: 'right', value: 'Quantum Threshold', fill: '#00ffaa', fontSize: 8 }} stroke="#00ffaa" strokeDasharray="5 5" />
                 <Line
                   type="monotone"
                   dataKey="s"
                   stroke="#00ffaa"
                   strokeWidth={2}
                   dot={false}
                   animationDuration={300}
                 />
               </LineChart>
             </ResponsiveContainer>
          </div>

          {/* Pre-flight & Setup */}
          <div className="space-y-4">
            <div className="bg-zinc-900/30 border border-arkhe-border rounded-xl p-4">
              <h3 className="text-[10px] font-mono text-arkhe-muted uppercase tracking-widest mb-4 flex items-center gap-2">
                <ShieldCheck className="w-3 h-3 text-arkhe-green" /> Pre-Flight Checks
              </h3>
              <div className="space-y-3">
                {Object.entries(chsh.preFlightChecks).map(([key, value]) => (
                  <div key={key} className="flex justify-between items-center text-[10px] font-mono">
                    <span className="text-arkhe-muted uppercase">{key.replace(/([A-Z])/g, ' $1')}</span>
                    <span className="text-arkhe-green font-bold">{(value as any)}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-zinc-900/30 border border-arkhe-border rounded-xl p-4">
              <h3 className="text-[10px] font-mono text-arkhe-muted uppercase tracking-widest mb-4 flex items-center gap-2">
                <Info className="w-3 h-3 text-arkhe-cyan" /> Measurement Setup
              </h3>
              <div className="space-y-2 text-[10px] font-mono">
                <div className="flex flex-col gap-1">
                  <span className="text-arkhe-muted uppercase">Instrument:</span>
                  <span className="text-white">{chsh.measurementSetup.instrument}</span>
                </div>
                <div className="flex flex-col gap-1">
                  <span className="text-arkhe-muted uppercase">Target System:</span>
                  <span className="text-white">{chsh.measurementSetup.targetSystem}</span>
                </div>
                <div className="flex flex-col gap-1">
                  <span className="text-arkhe-muted uppercase">Reference Lattice:</span>
                  <span className="text-white">{chsh.measurementSetup.referenceLattice}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Comment & Milestone */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-arkhe-cyan/5 border border-arkhe-cyan/20 p-4 rounded-xl relative overflow-hidden">
             <div className="absolute top-0 right-0 p-2 opacity-10">
               <Binary className="w-12 h-12 text-arkhe-cyan" />
             </div>
             <h3 className="text-[10px] font-mono text-arkhe-cyan uppercase tracking-widest mb-2 font-bold">Archimedes-Ω Commentary</h3>
             <p className="text-xs font-mono text-white leading-relaxed italic">
               "{chsh.archimedesComment}"
             </p>
          </div>

          <div className="bg-zinc-900/50 border border-arkhe-border p-4 rounded-xl flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="bg-arkhe-cyan/10 p-3 rounded-full">
                <Zap className="w-5 h-5 text-arkhe-cyan" />
              </div>
              <div>
                <div className="text-[10px] font-mono text-arkhe-muted uppercase">Next Milestone</div>
                <div className="text-xs font-bold font-mono text-white">{chsh.nextMilestone.action}</div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-[10px] font-mono text-arkhe-muted uppercase tracking-tighter">ETA (T-FIELD)</div>
              <div className="text-xs font-bold font-mono text-arkhe-cyan">
                {chsh.nextMilestone.time ? chsh.nextMilestone.time.split('T')[1].replace('Z', '') : '--:--:--'}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="px-6 py-2 bg-arkhe-cyan/5 border-t border-arkhe-cyan/10 text-right">
        <span className="text-[8px] font-mono text-arkhe-muted uppercase tracking-[0.3em]">
          Bio-Quantum Interface // Secure // Encrypted // Bell-Certified
        </span>
      </div>
    </div>
  );
}
