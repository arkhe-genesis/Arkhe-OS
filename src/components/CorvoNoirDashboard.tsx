
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Activity, Shield, Zap, Cpu, Heart, Fingerprint, Smile, Users, Radio } from 'lucide-react';
import React, { useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts';

import type { SimulationState } from '../../server/types';
import { useArkheSimulation } from '../hooks/useArkheSimulation';


import TemporalLensPanel from './TemporalLensPanel';

const CorvoNoirDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'coherence' | 'governance' | 'biolink' | 'security'>('coherence');
  const state: SimulationState = useArkheSimulation();

  // Simulated time-series data for the Kuramoto R(t)
  const chartData = React.useMemo(() => {
    return Array.from({ length: 20 }, (_, i) => ({
      time: i,
      coherence: state.currentLambda * (0.95 + Math.random() * 0.1),
      threat: state.threatLevel === 'critical' ? 0.8 : 0.1,
    }));
  }, [state.currentLambda, state.threatLevel]);

  const handleRegenerationPulse = async () => {
    try {
      await fetch('/api/governance/apply-regeneration-pulse', { method: 'POST' });
    } catch (err) {
      console.error(err);
    }
  };

  const handleStressTest = async () => {
    try {
      await fetch('/api/security/stress-test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ intensity: 0.7 })
      });
    } catch (err) {
      console.error(err);
    }
  };

  const handleGenerateManifesto = async () => {
    try {
      await fetch('/api/governance/manifesto', { method: 'POST' });
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="bg-neutral-950 text-neutral-100 p-6 rounded-xl border border-neutral-800 space-y-6 font-mono overflow-hidden">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold tracking-tighter text-neutral-50 flex items-center gap-2">
            <Activity className="text-emerald-500 w-6 h-6" />
            CORVO NOIR OS <span className="text-neutral-500 text-sm font-normal">v4.0.1-LUCENT</span>
          </h2>
          <p className="text-neutral-500 text-xs">AQUIFER COHERENCE REAL-TIME ANALYTICS</p>
        </div>
        <div className="flex gap-4">
          <div className="text-right">
            <p className="text-[10px] text-neutral-500 uppercase tracking-widest">Kuramoto R(t)</p>
            <p className={`text-xl font-bold ${state.currentLambda > 0.8 ? 'text-emerald-400' : 'text-amber-400'}`}>
              {(state.currentLambda * 100).toFixed(2)}%
            </p>
          </div>
          <div className="text-right">
            <p className="text-[10px] text-neutral-500 uppercase tracking-widest">Threat Level</p>
            <p className={`text-xl font-bold uppercase ${state.threatLevel === 'normal' ? 'text-emerald-400' : 'text-red-500'}`}>
              {state.threatLevel}
            </p>
          </div>
        </div>

        {/* Temporal Lens & Population Feedback */}
        <div className="lg:col-span-1">
          <TemporalLensPanel state={state} />
        </div>
      </div>

      <div className="flex gap-2 border-b border-neutral-800 pb-2">
        {(['coherence', 'governance', 'biolink', 'security'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`text-[10px] px-3 py-1 uppercase tracking-widest transition-colors ${activeTab === tab ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/50' : 'text-neutral-500 hover:text-neutral-300'}`}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* Main View Area */}
        <div className="lg:col-span-3 bg-neutral-900/50 p-4 rounded-lg border border-neutral-800 min-h-[300px]">
          {activeTab === 'coherence' && (
            <div className="h-64">
              <p className="text-[10px] text-neutral-400 mb-2 uppercase tracking-widest flex items-center gap-1">
                <Zap className="w-3 h-3 text-emerald-500" /> Phase Synchronization (θ)
              </p>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="colorCoh" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                  <XAxis dataKey="time" hide />
                  <YAxis domain={[0, 1.2]} hide />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#000', border: '1px solid #333', fontSize: '12px' }}
                    itemStyle={{ color: '#10b981' }}
                  />
                  <Area
                    type="monotone"
                    dataKey="coherence"
                    stroke="#10b981"
                    fillOpacity={1}
                    fill="url(#colorCoh)"
                    strokeWidth={2}
                    isAnimationActive={false}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}

          {activeTab === 'governance' && (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <p className="text-[10px] text-neutral-400 uppercase tracking-widest flex items-center gap-1">
                  <Smile className="w-3 h-3 text-amber-500" /> Matrix-Based Governance (Non-Hermitian)
                </p>
                <div className="flex gap-2">
                   <button onClick={handleRegenerationPulse} className="text-[8px] bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/50 px-2 py-1 uppercase">Apply Pulse</button>
                   <button onClick={handleGenerateManifesto} className="text-[8px] bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/50 px-2 py-1 uppercase">Manifesto 2027</button>
                </div>
              </div>

              <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
                <div className="bg-black/40 p-3 rounded border border-neutral-800">
                   <p className="text-[9px] text-neutral-500 uppercase mb-1">Global Happiness Index</p>
                   <p className="text-xl font-bold text-amber-400">{(state.grossHappiness?.globalIndex || 0).toFixed(2)}%</p>
                   <div className="w-full bg-neutral-800 h-1 mt-2">
                      <div className="bg-amber-500 h-full" style={{ width: `${state.grossHappiness?.globalIndex || 0}%` }}></div>
                   </div>
                </div>
                <div className="bg-black/40 p-3 rounded border border-neutral-800">
                   <p className="text-[9px] text-neutral-500 uppercase mb-1">λ₁ (Material Evolution)</p>
                   <p className="text-xl font-bold text-amber-200">{state.governanceManifesto?.eigenvalues?.[0] || '1.1800'}</p>
                </div>
                <div className="bg-black/40 p-3 rounded border border-neutral-800">
                   <p className="text-[9px] text-neutral-500 uppercase mb-1">λ₂ (Social Coherence)</p>
                   <p className="text-xl font-bold text-emerald-400">{state.governanceManifesto?.eigenvalues?.[1] || '1.0600'}</p>
                </div>
              </div>

              {state.governanceManifesto && (
                <div className="bg-amber-950/20 border border-amber-500/30 p-4 rounded">
                  <p className="text-xs font-bold text-amber-500 mb-2">MANIFESTO DE GOVERNANÇA 2027 (ACTIVE)</p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {Object.entries(state.governanceManifesto.sectors as Record<string, string>).map(([sector, desc]) => (
                      <div key={sector} className="text-[10px]">
                        <span className="text-amber-500/60 uppercase">{sector}:</span> <span className="text-amber-200/80">{desc}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'biolink' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <p className="text-[10px] text-neutral-400 uppercase tracking-widest flex items-center gap-1">
                  <Users className="w-3 h-3 text-blue-500" /> Population Bio-Link (Ritmo Gama 40Hz)
                </p>
                <div className="bg-blue-500/10 text-blue-400 border border-blue-500/50 px-2 py-0.5 text-[8px] uppercase animate-pulse">
                   Vigilância Ativa
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <p className="text-[10px] text-neutral-500 uppercase mb-1 flex justify-between">
                      Mass Synchronization <span>{(state.bioLinkSync.syncRatio * 100).toFixed(1)}%</span>
                    </p>
                    <div className="w-full bg-neutral-800 h-2 rounded-full overflow-hidden">
                      <div className="bg-blue-500 h-full transition-all duration-1000" style={{ width: `${state.bioLinkSync.syncRatio * 100}%` }}></div>
                    </div>
                  </div>
                  <div>
                    <p className="text-[10px] text-neutral-500 uppercase mb-1 flex justify-between">
                      Cellular Regeneration Pulse <span>{(state.bioLinkSync.regenerationProgress).toFixed(1)}%</span>
                    </p>
                    <div className="w-full bg-neutral-800 h-2 rounded-full overflow-hidden">
                      <div className="bg-emerald-500 h-full transition-all duration-1000" style={{ width: `${state.bioLinkSync.regenerationProgress}%` }}></div>
                    </div>
                  </div>
                  <div className="bg-blue-900/10 p-3 rounded border border-blue-800/30">
                    <p className="text-[10px] text-blue-400 font-bold mb-1">MAXTOKI FEEDBACK CHANNEL</p>
                    <p className="text-[9px] text-blue-300/70">13,000 residents in Urca/Flamengo are currently interacting with their 2027 instances. Coherence gain: <span className="text-white">x{state.bioLinkSync.coherenceGain.toFixed(2)}</span></p>
                  </div>
                </div>

                <div className="bg-black/20 p-4 rounded border border-neutral-800 flex flex-col justify-center items-center">
                   <Radio className="w-12 h-12 text-blue-500 animate-ping opacity-20 mb-4" />
                   <p className="text-2xl font-bold text-blue-400">40.0 Hz</p>
                   <p className="text-[9px] text-neutral-500 uppercase tracking-widest mt-1">Interstate Phase Carrier</p>
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
                   {state.sensors.map((s: any) => (
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

        {/* System Stats Sidebar */}
        <div className="space-y-4">
          <div className="bg-neutral-900/50 p-4 rounded-lg border border-neutral-800">
            <div className="flex items-center gap-3 mb-2">
              <Shield className="w-5 h-5 text-blue-500" />
              <p className="text-xs font-bold uppercase tracking-widest">Security Substrate</p>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-[10px]">
                <span className="text-neutral-500">ZK-PROOF INTEGRITY</span>
                <span className={state.security.zkProofValid ? 'text-emerald-400' : 'text-red-400'}>
                  {state.security.zkProofValid ? 'VERIFIED' : 'FAILED'}
                </span>
              </div>
              <div className="w-full bg-neutral-800 h-1 rounded-full overflow-hidden">
                <div className="bg-emerald-500 h-full" style={{ width: '92%' }}></div>
              </div>
              <div className="flex justify-between text-[10px]">
                <span className="text-neutral-500">YANG-BAXTER TOPOLOGY</span>
                <span className={state.topology.yangBaxterValid ? 'text-emerald-400' : 'text-red-400'}>
                  {state.topology.yangBaxterValid ? 'STABLE' : 'UNSTABLE'}
                </span>
              </div>
              <div className="w-full bg-neutral-800 h-1 rounded-full overflow-hidden">
                <div className="bg-emerald-500 h-full" style={{ width: '100%' }}></div>
              </div>
            </div>
          </div>

          <div className="bg-neutral-900/50 p-4 rounded-lg border border-neutral-800">
            <div className="flex items-center gap-3 mb-2">
              <Cpu className="w-5 h-5 text-purple-500" />
              <p className="text-xs font-bold uppercase tracking-widest">Hardware Layer</p>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div className="bg-black/40 p-2 rounded">
                <p className="text-[8px] text-neutral-500 uppercase">TMR Faults</p>
                <p className="text-sm font-bold text-neutral-300">{state.hardware.tmrFaultsCorrected}</p>
              </div>
              <div className="bg-black/40 p-2 rounded">
                <p className="text-[8px] text-neutral-500 uppercase">Shards Active</p>
                <p className="text-sm font-bold text-neutral-300">{state.mitigation.tzinorShardsAvailable}/24</p>
              </div>
            </div>
          </div>

          {/* Wetware Biometrics Sidebar */}
          <div className="bg-neutral-900/50 p-4 rounded-lg border border-neutral-800">
            <div className="flex items-center gap-3 mb-2">
              <Fingerprint className="w-5 h-5 text-emerald-500" />
              <p className="text-xs font-bold uppercase tracking-widest text-emerald-500">Wetware Biometrics</p>
            </div>
            {state.biometrics ? (
              <div className="space-y-3">
                <div className="flex justify-between items-end">
                  <div>
                    <p className="text-[8px] text-neutral-500 uppercase">Liveness Score</p>
                    <p className={`text-lg font-bold ${(state.biometrics.livenessScore || 0) > 0.8 ? 'text-emerald-400' : 'text-red-400'}`}>
                      {((state.biometrics.livenessScore || 0) * 100).toFixed(1)}%
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-[8px] text-neutral-500 uppercase">Status</p>
                    <p className={`text-xs font-bold uppercase ${state.biometrics.isAuthentic ? 'text-emerald-400' : 'text-red-400'}`}>
                      {state.biometrics.isAuthentic ? 'AUTHENTIC' : 'UNAUTHORIZED'}
                    </p>
                  </div>
                </div>

                <div>
                  <p className="text-[8px] text-neutral-500 uppercase mb-1 flex items-center gap-1">
                    <Heart className="w-2 h-2 text-red-500" /> Heartbeat Coherence
                  </p>
                  <div className="w-full bg-neutral-800 h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-red-500 h-full transition-all duration-500"
                      style={{ width: `${(state.biometrics.heartbeatCoherence || 0) * 100}%` }}
                    ></div>
                  </div>
                </div>

                {state.biometrics.phaseSignature && (
                  <div>
                    <p className="text-[8px] text-neutral-500 uppercase mb-1">Phase Signature</p>
                    <div className="flex gap-0.5 h-4 items-end">
                      {(state.biometrics.phaseSignature as number[]).map((val: number, idx: number) => (
                        <div
                          key={idx}
                          className="bg-emerald-500/50 flex-1 hover:bg-emerald-500 transition-colors"
                          style={{ height: `${val * 100}%` }}
                        ></div>
                      ))}
                    </div>
                  </div>
                )}

                <p className="text-[7px] text-neutral-600 uppercase text-center italic">
                  Last verified: {state.biometrics.lastVerification ? new Date(state.biometrics.lastVerification as number).toLocaleTimeString() : 'N/A'}
                </p>
              </div>
            ) : (
              <p className="text-[10px] text-neutral-500 italic">No biometric data available.</p>
            )}
          </div>
        </div>
      </div>

      <div className="bg-black/80 border border-neutral-800 rounded p-3 h-32 overflow-y-auto scrollbar-hide">
        <p className="text-[10px] text-neutral-500 mb-2 font-bold tracking-widest uppercase">System Log (CORVO_OS_KERNEL)</p>
        {state.logs.slice(0, 10).map((log) => (
          <div key={log.id} className="flex gap-2 mb-1">
            <span className="text-neutral-600 text-[10px] shrink-0">[{new Date(log.originTime || 0).toLocaleTimeString()}]</span>
            <span className={`text-[10px] ${log.status === 'Valid' ? 'text-neutral-400' : 'text-red-400'}`}>
              {log.threatType || (log.status === 'Valid' ? 'NOMINAL OPERATION' : 'ANOMALY')}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CorvoNoirDashboard;
