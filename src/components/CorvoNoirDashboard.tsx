
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Activity, Shield, Zap, Cpu, Heart, Fingerprint, Smile, Users, Radio, Aperture } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import React, { useState } from 'react';
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip
} from 'recharts';

import type { SimulationState } from '../../server/types';
import { useArkheSimulation } from '../hooks/useArkheSimulation';
import { Card } from './ui/Card';
import { Progress } from './ui/Progress';
import { Badge } from './ui/Badge';
import { cn } from '../lib/utils';

import TemporalLensPanel from './TemporalLensPanel';

const CorvoNoirDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'coherence' | 'governance' | 'biolink' | 'security'>('coherence');
  const state: SimulationState = useArkheSimulation();

  const isOmegaSymmetry = state.currentLambda > 0.99;
  const hasCriticalAnomaly = state.threatLevel === 'critical';

  // Simulated time-series data
  const chartData = React.useMemo(() => {
    return Array.from({ length: 20 }, (_, i) => ({
      time: i,
      coherence: state.currentLambda * (0.95 + Math.random() * 0.1),
      threat: state.threatLevel === 'critical' ? 0.8 : 0.1,
    }));
  }, [state.currentLambda, state.threatLevel]);

  const handleRegenerationPulse = () => fetch('/api/governance/apply-regeneration-pulse', { method: 'POST' });

  return (
    <div className="space-y-6 ricci-flow">
      {/* Header Section */}
      <div className="flex justify-between items-center bg-black/40 p-6 rounded-xl border border-white/5 glass-hilbert">
        <div className="space-y-1">
          <motion.h2
            animate={isOmegaSymmetry ? { color: ['#00E5FF', '#FFFFFF', '#00E5FF'] } : {}}
            transition={{ duration: 4, repeat: Infinity }}
            className="text-golden-base font-bold tracking-tighter flex items-center gap-3 kerning-fibonacci"
          >
            <Aperture className={isOmegaSymmetry ? "text-white animate-spin-slow" : "text-arkhe-cerenkov"} />
            CORVO NOIR <span className="text-arkhe-muted font-light">OS v4.2</span>
          </motion.h2>
          <p className="text-golden-xs text-arkhe-muted uppercase tracking-[0.2em] font-serif italic">
            Manifold Invariance: {isOmegaSymmetry ? 'PONTO ÔMEGA' : 'ESTÁVEL'}
          </p>
        </div>

        <div className="flex gap-8">
          <div className="text-right">
            <p className="text-golden-xs text-arkhe-muted uppercase tracking-widest">Sincronia θ</p>
            <p className={`text-golden-sm font-bold kerning-fibonacci ${state.currentLambda > 0.8 ? 'text-arkhe-cerenkov' : 'text-arkhe-amber'}`}>
              {(state.currentLambda * 100).toFixed(2)}%
            </p>
          </div>
          <div className="text-right">
            <p className="text-golden-xs text-arkhe-muted uppercase tracking-widest">Integridade</p>
            <p className={`text-golden-sm font-bold uppercase ${!hasCriticalAnomaly ? 'text-arkhe-teal' : 'text-arkhe-fissure fissure-glow'}`}>
              {state.threatLevel}
            </p>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex gap-4 border-b border-white/5 pb-2">
        {(['coherence', 'governance', 'biolink', 'security'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={cn(
              "text-golden-xs px-4 py-2 uppercase tracking-[0.15em] transition-all relative",
              activeTab === tab ? "text-arkhe-cerenkov" : "text-arkhe-muted hover:text-white"
            )}
          >
            {tab}
            {activeTab === tab && (
              <motion.div layoutId="tab-underline" className="absolute bottom-0 left-0 w-full h-0.5 bg-arkhe-cerenkov" />
            )}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content Area */}
        <div className="lg:col-span-2 space-y-6">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 10 }}
              className="min-h-[400px]"
            >
              {activeTab === 'coherence' && (
                <Card variant="hilbert" title="Hilbert Space Wavefunction" icon={<Zap className="w-3 h-3 text-arkhe-cerenkov" />}>
                  <div className="h-64 mt-4">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={chartData}>
                        <defs>
                          <linearGradient id="colorCoh" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="var(--color-arkhe-cerenkov)" stopOpacity={0.3}/>
                            <stop offset="95%" stopColor="var(--color-arkhe-cerenkov)" stopOpacity={0}/>
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                        <XAxis dataKey="time" hide />
                        <YAxis domain={[0, 1.2]} hide />
                        <Tooltip
                          contentStyle={{ backgroundColor: 'rgba(0,0,0,0.8)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                          itemStyle={{ color: 'var(--color-arkhe-cerenkov)' }}
                        />
                        <Area
                          type="monotone"
                          dataKey="coherence"
                          stroke="var(--color-arkhe-cerenkov)"
                          fillOpacity={1}
                          fill="url(#colorCoh)"
                          strokeWidth={2}
                          isAnimationActive={false}
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="mt-4 grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <p className="text-[10px] text-arkhe-muted uppercase">Phase Variance</p>
                      <Progress value={state.currentLambda * 100} color="cerenkov" />
                    </div>
                    <div className="space-y-1">
                      <p className="text-[10px] text-arkhe-muted uppercase">Noise Floor</p>
                      <Progress value={15} color="cyan" />
                    </div>
                  </div>
                </Card>
              )}

              {activeTab === 'security' && (
                <div className="space-y-6">
                  <Card
                    variant="base"
                    status={hasCriticalAnomaly ? 'critical' : 'normal'}
                    title="Chronos-Guard / Temporal Shield"
                    icon={<Shield className="w-3 h-3 text-arkhe-fissure" />}
                  >
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="p-3 bg-white/5 rounded border border-white/5">
                        <p className="text-[8px] text-arkhe-muted uppercase">TII Factor</p>
                        <p className={cn("text-lg font-bold", state.temporalAudit.lastTII > 0.05 ? "text-arkhe-fissure" : "text-arkhe-teal")}>
                          {state.temporalAudit.lastTII.toFixed(4)}
                        </p>
                      </div>
                      <div className="p-3 bg-white/5 rounded border border-white/5">
                        <p className="text-[8px] text-arkhe-muted uppercase">Collapse Risk</p>
                        <p className="text-lg font-bold text-arkhe-amber">
                          {(state.predictiveForecast.coherenceCollapseRisk * 100).toFixed(1)}%
                        </p>
                      </div>
                      <div className="p-3 bg-white/5 rounded border border-white/5">
                        <p className="text-[8px] text-arkhe-muted uppercase">Active Shards</p>
                        <p className="text-lg font-bold">{state.mitigation.tzinorShardsAvailable}/24</p>
                      </div>
                      <div className="p-3 bg-white/5 rounded border border-white/5">
                        <p className="text-[8px] text-arkhe-muted uppercase">ZK Integrity</p>
                        <Badge color={state.security.zkProofValid ? 'cyan' : 'fissure'}>
                          {state.security.zkProofValid ? 'VERIFIED' : 'BREACH'}
                        </Badge>
                      </div>
                    </div>
                  </Card>

                  {/* Fractal Analysis Area */}
                  <div className="p-6 rounded-xl border border-white/5 glass-hilbert relative overflow-hidden">
                    <div className="absolute inset-0 fractal-noise" />
                    <div className="relative z-10 flex items-center justify-between">
                      <div className="space-y-1">
                        <h4 className="text-golden-sm font-bold uppercase kerning-fibonacci">Análise Fractal Profunda</h4>
                        <p className="text-golden-xs text-arkhe-muted">Mapeando geodésicas de não-localidade...</p>
                      </div>
                      <div className="w-16 h-16 rounded-full border-2 border-dashed border-arkhe-cerenkov animate-spin-slow flex items-center justify-center">
                        <div className="w-10 h-10 rounded-full border border-arkhe-cerenkov/50 animate-pulse" />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'biolink' && (
                <div className="space-y-6">
                  <Card variant="liquid" title="Population Bio-Sync" icon={<Users className="w-3 h-3 text-lumina-violet" />}>
                    <div className="space-y-6">
                       <div className="flex items-center justify-between">
                         <div className="flex items-center gap-4">
                           <div className="w-12 h-12 rounded-full border border-lumina-violet/30 flex items-center justify-center bg-lumina-violet/10">
                              <Radio className="w-6 h-6 text-lumina-violet animate-pulse" />
                           </div>
                           <div>
                             <p className="text-lg font-bold font-serif italic text-white">40.0 Hz</p>
                             <p className="text-golden-xs text-arkhe-muted uppercase tracking-widest">Gamma Carrier Frequency</p>
                           </div>
                         </div>
                         <Badge color="omega" variant="glass">Active Mesh</Badge>
                       </div>

                       <div className="space-y-4">
                         <div className="space-y-1">
                            <div className="flex justify-between text-[10px] uppercase">
                              <span className="text-arkhe-muted">Synchronization Ratio</span>
                              <span className="text-white">{(state.bioLinkSync.syncRatio * 100).toFixed(1)}%</span>
                            </div>
                            <Progress value={state.bioLinkSync.syncRatio * 100} color="cerenkov" />
                         </div>
                         <div className="space-y-1">
                            <div className="flex justify-between text-[10px] uppercase">
                              <span className="text-arkhe-muted">Regeneration Progress</span>
                              <span className="text-white">{(state.bioLinkSync.regenerationProgress).toFixed(1)}%</span>
                            </div>
                            <Progress value={state.bioLinkSync.regenerationProgress} color="cyan" />
                         </div>
                       </div>
                    </div>
                  </Card>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="space-y-4">
               <div className="flex justify-between items-center">
                <p className="text-[10px] text-neutral-400 uppercase tracking-widest flex items-center gap-1">
                  <Shield className="w-3 h-3 text-red-500" /> Chronos-Guard (Temporal Shield v2.1-Σ)
                </p>
                <button onClick={handleStressTest} className="text-[8px] bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/50 px-2 py-1 uppercase">Stress Test</button>
              </div>

              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                 <div className="bg-black/40 p-2 rounded border border-neutral-800">
                    <p className="text-[8px] text-neutral-500 uppercase">Temporal Inconsistency (TII)</p>
                    <p className={`text-lg font-bold ${state.temporalAudit.lastTII > 0.05 ? 'text-red-500' : 'text-emerald-400'}`}>
                      {state.temporalAudit.lastTII.toFixed(4)}
                    </p>
                 </div>
                 <div className="bg-black/40 p-2 rounded border border-neutral-800">
                    <p className="text-[8px] text-neutral-500 uppercase">Locked Events</p>
                    <p className="text-lg font-bold text-neutral-100">{state.temporalAudit.lockedEvents}</p>
                 </div>
                 <div className="bg-black/40 p-2 rounded border border-neutral-800">
                    <p className="text-[8px] text-neutral-500 uppercase">Collapse Risk</p>
                    <p className={`text-lg font-bold ${state.predictiveForecast.coherenceCollapseRisk > 0.3 ? 'text-red-500' : 'text-emerald-400'}`}>
                      {(state.predictiveForecast.coherenceCollapseRisk * 100).toFixed(1)}%
                    </p>
                 </div>
                 <div className="bg-black/40 p-2 rounded border border-neutral-800">
                    <p className="text-[8px] text-neutral-500 uppercase">Forecast λ₂</p>
                    <p className="text-lg font-bold text-blue-400">{state.predictiveForecast.predictedLambda.toFixed(4)}</p>
                 </div>
              </div>

              <div className="bg-neutral-900 p-3 rounded border border-neutral-800 h-32 overflow-hidden relative">
                 <div className="flex gap-1 h-full items-end">
                   {state.sensors.map((s) => (
                     <div
                       key={s.id}
                       className={`w-1 transition-all ${s.status === 'attacked' ? 'bg-red-500 animate-pulse' : s.status === 'isolated' ? 'bg-neutral-700' : 'bg-emerald-500/40'}`}
                       style={{ height: `${(s.value / 5.0) * 100}%`, minHeight: '2px' }}
                     />
                   ))}
                 </div>
                 <div className="absolute inset-0 bg-gradient-to-t from-neutral-900 to-transparent pointer-events-none" />
                 <p className="absolute top-2 left-2 text-[8px] text-neutral-500 uppercase font-bold">168 NV SENSOR GRID (C-DOMAIN)</p>
              </div>
            </div>
          )}
        </div>

        {/* Sidebar Stats */}
        <div className="space-y-6">
           <Card variant="base" title="System Vitality" icon={<Activity className="w-3 h-3 text-arkhe-teal" />}>
             <div className="space-y-4 mt-2">
                <div className="flex justify-between items-center">
                  <span className="text-[10px] text-arkhe-muted uppercase">Liveness</span>
                  <span className="text-sm font-bold text-arkhe-teal">{((state.biometrics?.livenessScore || 0) * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[10px] text-arkhe-muted uppercase">Coherence Gain</span>
                  <span className="text-sm font-bold text-arkhe-cerenkov">x{state.bioLinkSync.coherenceGain.toFixed(2)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[10px] text-arkhe-muted uppercase">TMR Corrected</span>
                  <span className="text-sm font-bold text-white">{state.hardware.tmrFaultsCorrected}</span>
                </div>
             </div>
           </Card>

           <div className="p-4 rounded-xl border border-white/5 glass-hilbert">
              <h4 className="text-[10px] font-bold text-arkhe-muted uppercase tracking-widest mb-4">Kernel Real-time Log</h4>
              <div className="space-y-2 h-48 overflow-y-auto pr-2 custom-scrollbar">
                {state.logs.slice(0, 15).map((log) => (
                  <div key={log.id} className="text-[9px] font-mono flex gap-2 border-b border-white/5 pb-1">
                    <span className="text-arkhe-muted whitespace-nowrap">[{new Date(log.originTime || 0).toLocaleTimeString()}]</span>
                    <span className={cn(log.status === 'Valid' ? 'text-arkhe-muted' : 'text-arkhe-fissure')}>
                      {log.threatType || 'NOMINAL_FLOW'}
                    </span>
                  </div>
                ))}
              </div>
           </div>

           <TemporalLensPanel state={state} />
        </div>
      </div>
    </div>
  );
};

export default CorvoNoirDashboard;
