
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Cpu, Shield, Zap, RefreshCw, HardDrive } from 'lucide-react';

import { Card } from './ui/Card';


interface MitigationEngineProps {
  mitigation: {
    nullSteeringActive: boolean;
    kuramotoSyncPhase: number;
  };
  hardware: {
    tmrFaultsCorrected: number;
    bramScrubbingActive: boolean;
  };
  activeThreat: string | null;
}

export default function MitigationEngine({ mitigation, hardware, activeThreat }: MitigationEngineProps) {
  return (
    <Card
      title="Aegis-MT (Mitigation)"
      icon={<Cpu className="w-4 h-4" />}
      status={activeThreat ? 'warning' : 'normal'}
    >
      <div className="space-y-4">
        {/* Active Threat Display */}
        <div className={`p-3 rounded border ${activeThreat ? 'bg-arkhe-red/10 border-arkhe-red/30' : 'bg-[#151619] border-arkhe-border'}`}>
          <div className="text-xs font-mono text-arkhe-muted uppercase mb-1">Active Threat Vector</div>
          <div className={`text-sm font-mono font-bold ${activeThreat ? 'text-arkhe-red glitch' : 'text-arkhe-green'}`}>
            {activeThreat ? `[DETECTED] ${activeThreat.toUpperCase()}` : 'NONE'}
          </div>
        </div>

        {/* Mitigation Systems */}
        <div className="grid grid-cols-2 gap-3">
          <div className={`p-3 rounded border ${mitigation.nullSteeringActive ? 'bg-arkhe-cyan/10 border-arkhe-cyan/30' : 'bg-[#151619] border-arkhe-border'}`}>
            <div className="flex items-center gap-2 mb-2">
              <Shield className={`w-3 h-3 ${mitigation.nullSteeringActive ? 'text-arkhe-cyan' : 'text-arkhe-muted'}`} />
              <span className="text-[10px] font-mono text-arkhe-muted uppercase">Null Steering</span>
            </div>
            <div className={`text-xs font-mono font-bold ${mitigation.nullSteeringActive ? 'text-arkhe-cyan' : 'text-arkhe-muted'}`}>
              {mitigation.nullSteeringActive ? 'ACTIVE' : 'STANDBY'}
            </div>
          </div>

          <div className="p-3 rounded border bg-[#151619] border-arkhe-border relative overflow-hidden">
            <div className="flex items-center gap-2 mb-2 relative z-10">
              <Zap className="w-3 h-3 text-arkhe-orange" />
              <span className="text-[10px] font-mono text-arkhe-muted uppercase">Kuramoto Sync</span>
            </div>
            <div className="text-xs font-mono font-bold text-arkhe-orange relative z-10">
              φ = {mitigation.kuramotoSyncPhase.toFixed(2)} rad
            </div>
            {/* Sync visualization background */}
            <div
              className="absolute bottom-0 left-0 h-1 bg-arkhe-orange/30 w-full"
            >
              <div
                className="h-full bg-arkhe-orange transition-all duration-100"
                style={{ width: `${(mitigation.kuramotoSyncPhase / (2 * Math.PI)) * 100}%` }}
              />
            </div>
          </div>
        </div>

        {/* Hardware Resilience (TMR & BRAM) */}
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 rounded border bg-[#151619] border-arkhe-border">
            <div className="flex items-center gap-2 mb-2">
              <RefreshCw className={`w-3 h-3 ${hardware.tmrFaultsCorrected > 0 ? 'text-arkhe-orange animate-spin' : 'text-arkhe-muted'}`} />
              <span className="text-[10px] font-mono text-arkhe-muted uppercase">TMR Faults</span>
            </div>
            <div className={`text-xs font-mono font-bold ${hardware.tmrFaultsCorrected > 0 ? 'text-arkhe-orange' : 'text-arkhe-green'}`}>
              {hardware.tmrFaultsCorrected} CORRECTED
            </div>
          </div>
          <div className="p-3 rounded border bg-[#151619] border-arkhe-border">
            <div className="flex items-center gap-2 mb-2">
              <HardDrive className={`w-3 h-3 ${hardware.bramScrubbingActive ? 'text-arkhe-cyan' : 'text-arkhe-muted'}`} />
              <span className="text-[10px] font-mono text-arkhe-muted uppercase">BRAM Scrub</span>
            </div>
            <div className={`text-xs font-mono font-bold ${hardware.bramScrubbingActive ? 'text-arkhe-cyan' : 'text-arkhe-muted'}`}>
              {hardware.bramScrubbingActive ? '1 Hz ACTIVE' : 'DISABLED'}
            </div>
          </div>
        </div>

        {/* OAM Signature */}
        <div className="p-3 rounded border bg-[#151619] border-arkhe-border">
          <div className="text-xs font-mono text-arkhe-muted uppercase mb-2">OAM Signature (ℓ)</div>
          <div className="flex gap-1 h-8">
            {Array.from({ length: 16 }).map((_, i) => {
              // Generate a pseudo-random pattern based on the sync phase
              const isActive = Math.sin(mitigation.kuramotoSyncPhase * (i + 1)) > 0;
              return (
                <div
                  key={i}
                  className={`flex-1 rounded-sm transition-colors duration-200 ${isActive ? 'bg-arkhe-cyan' : 'bg-[#1f2024]'}`}
                />
              );
            })}
          </div>
        </div>
      </div>
    </Card>
  );
}
