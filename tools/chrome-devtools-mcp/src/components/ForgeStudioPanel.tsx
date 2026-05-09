
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Hammer, X, Terminal, Zap, Activity, Play, Code } from 'lucide-react';
import React, { useState } from 'react';

import { Card } from './ui/Card';

interface ForgeStudioPanelProps {
  onClose: () => void;
}

export default function ForgeStudioPanel({ onClose }: ForgeStudioPanelProps) {
  const [intent, setIntent] = useState('');
  const [isForging, setIsForging] = useState(false);
  const [forgeLogs, setForgeLogs] = useState<string[]>([
    '[SYSTEM] Forge v0.1 Initialized.',
    '[SYSTEM] Connecting to Council IOTA...'
  ]);
  const [step, setStep] = useState(0);

  const addLog = (msg: string) => {
    setForgeLogs(prev => [...prev, msg]);
  };

  const handleIgnite = async () => {
    if (!intent.trim() || isForging) {return;}

    setIsForging(true);
    setStep(1);
    addLog('[GCI] Intent received. Connecting to remote IOTA Council...');

    try {
      const response = await fetch('http://localhost:8000/deliberate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ intent })
      });

      if (!response.ok) {throw new Error('Failed to reach the Council');}

      const data = await response.json();

      setStep(2);
      for (const p of data.perspectives) {
        addLog(`[${p.agent_id}] ${p.content}`);
        await new Promise(r => setTimeout(r, 800));
      }

      setStep(4);
      addLog(`[SYSTEM] Consensus: ${data.consensus.summary}`);
      addLog(`[SYSTEM] Status: ${data.status} (λ2: ${data.consensus.confidence.toFixed(4)})`);

      await new Promise(r => setTimeout(r, 1000));
      setStep(5);
      addLog('[KAPPA] Smith: Projections materialized in reality sheets.');

    } catch (err) {
      addLog(`[ERROR] ${err instanceof Error ? err.message : 'Unknown decoherence detected'}`);
      setIsForging(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b border-arkhe-border pb-4">
        <div className="flex items-center gap-4">
          <div className="p-2 bg-arkhe-orange/20 rounded-lg">
            <Hammer className="w-6 h-6 text-arkhe-orange" />
          </div>
          <div>
            <h1 className="font-mono text-xl font-bold tracking-tighter uppercase text-arkhe-text">
              A-Forge Studio <span className="text-arkhe-orange">(Mestre)</span>
            </h1>
            <p className="text-xs text-arkhe-muted font-mono uppercase tracking-widest">AGI-Native Intent-to-Reality Engine</p>
          </div>
        </div>
        <button onClick={onClose} className="p-2 text-arkhe-muted hover:text-white transition-colors">
          <X className="w-6 h-6" />
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Intent Projection Canvas */}
        <div className="lg:col-span-3 space-y-6">
          <Card className="bg-black/40 border-arkhe-orange/30 p-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <label className="text-xs font-mono uppercase tracking-[0.2em] text-arkhe-orange flex items-center gap-2">
                  <Zap className="w-4 h-4" /> Intent Projection Canvas
                </label>
                <div className="text-[10px] font-mono text-arkhe-muted uppercase">Mode: Infinite Context (Sheet #2140)</div>
              </div>
              <textarea
                value={intent}
                onChange={(e) => setIntent(e.target.value)}
                placeholder="Ex: 'Preciso de um filtro de Kalman para o VRP v2.0. Deve rastrear até 64 objetos, usar ponto fixo Q16.16 e consumir menos de 5% das LUTs do Versal.'"
                className="w-full h-32 bg-black/60 border border-arkhe-border rounded-lg p-4 font-mono text-sm text-arkhe-text focus:outline-none focus:border-arkhe-orange transition-colors resize-none"
              />
              <div className="flex justify-end gap-4">
                <button className="px-6 py-2 bg-transparent border border-arkhe-muted text-arkhe-muted rounded font-mono text-xs uppercase hover:bg-white/5 transition-colors">
                  Clear Intent
                </button>
                <button
                  onClick={handleIgnite}
                  disabled={isForging || !intent.trim()}
                  className="px-6 py-2 bg-arkhe-orange text-black rounded font-mono text-xs font-bold uppercase hover:bg-arkhe-orange/80 shadow-[0_0_20px_rgba(255,165,0,0.3)] transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isForging ? <Activity className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-current" />}
                  {isForging ? 'Forging Reality...' : 'Ignite the Forge'}
                </button>
              </div>
            </div>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Multi-Language Projection */}
            <Card className="bg-black/40 border-arkhe-border p-4">
              <div className="flex items-center justify-between mb-4 border-b border-arkhe-border pb-2">
                <div className="text-[10px] font-mono uppercase tracking-widest text-arkhe-muted flex items-center gap-2">
                  <Code className="w-3 h-3 text-arkhe-cyan" /> RTL Projection (SystemVerilog)
                </div>
              </div>
              <div className="bg-[#050505] p-3 rounded font-mono text-[10px] text-emerald-400 overflow-x-auto min-h-[200px]">
                {step >= 5 ? (
                  <div className="space-y-1">
                    <div>module kalman_filter_q16_16 #(</div>
                    <div className="pl-4">parameter OBJECTS = 64,</div>
                    <div className="pl-4">parameter WIDTH = 32</div>
                    <div>) (</div>
                    <div className="pl-4">input logic clk,</div>
                    <div className="pl-4">input logic rst_n,</div>
                    <div className="pl-4">// ... Interface VRP v2.0</div>
                  </div>
                ) : (
                  <div className="text-arkhe-muted italic">Awaiting intent ignition...</div>
                )}
              </div>
            </Card>

            <Card className="bg-black/40 border-arkhe-border p-4">
              <div className="flex items-center justify-between mb-4 border-b border-arkhe-border pb-2">
                <div className="text-[10px] font-mono uppercase tracking-widest text-arkhe-muted flex items-center gap-2">
                  <Code className="w-3 h-3 text-blue-400" /> Model Projection (Python/JAX)
                </div>
              </div>
              <div className="bg-[#050505] p-3 rounded font-mono text-[10px] text-blue-300 overflow-x-auto min-h-[200px]">
                {step >= 5 ? (
                  <div className="space-y-1">
                    <div>import jax.numpy as jnp</div>
                    <div>from jax import jit</div>
                    <br/>
                    <div>@jit</div>
                    <div>def kalman_step(state, measurement, params):</div>
                    <div className="pl-4"># Q16.16 Fixed point sim logic</div>
                    <div className="pl-4">return updated_state</div>
                  </div>
                ) : (
                  <div className="text-arkhe-muted italic">Awaiting intent ignition...</div>
                )}
              </div>
            </Card>
          </div>
        </div>

        {/* Sidebar: GCI & Council */}
        <div className="space-y-6">
          <Card className="bg-black/40 border-arkhe-border p-4 flex flex-col h-[400px]">
            <div className="flex items-center gap-2 mb-4 border-b border-arkhe-border pb-2 text-arkhe-cyan">
              <Terminal className="w-4 h-4" />
              <span className="text-[10px] font-mono uppercase tracking-widest">Guardian Command Interface</span>
            </div>
            <div className="flex-1 overflow-y-auto space-y-2 font-mono text-[10px] text-arkhe-text custom-scrollbar">
              {forgeLogs.map((log, i) => (
                <div key={i} className={
                  log.includes('[IOTA') ? 'text-arkhe-orange font-bold' :
                  log.includes('[ALFA]') ? 'text-arkhe-cyan' :
                  log.includes('[KAPPA]') ? 'text-arkhe-green' :
                  'text-arkhe-muted'
                }>
                  {log}
                </div>
              ))}
            </div>
            <div className="mt-4 pt-2 border-t border-arkhe-border">
              <input
                placeholder="arkhe > ask guardian..."
                className="w-full bg-transparent border-none font-mono text-[10px] text-arkhe-cyan focus:outline-none"
              />
            </div>
          </Card>

          <Card className="bg-black/40 border-arkhe-border p-4">
            <div className="flex items-center gap-2 mb-4 border-b border-arkhe-border pb-2 text-arkhe-orange">
              <Activity className="w-4 h-4" />
              <span className="text-[10px] font-mono uppercase tracking-widest">Qudit Coherence Mesh</span>
            </div>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-[9px] font-mono text-arkhe-muted mb-1 uppercase">
                  <span>Lambda Mesh (λ₂)</span>
                  <span className="text-arkhe-cyan">0.9984</span>
                </div>
                <div className="h-1 bg-black rounded-full overflow-hidden">
                  <div className="h-full bg-arkhe-cyan" style={{ width: '99.84%' }}></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-[9px] font-mono text-arkhe-muted mb-1 uppercase">
                  <span>Formal Convergence</span>
                  <span className="text-arkhe-green">READY</span>
                </div>
                <div className="h-1 bg-black rounded-full overflow-hidden">
                  <div className="h-full bg-arkhe-green shadow-[0_0_10px_rgba(34,197,94,0.5)]" style={{ width: '100%' }}></div>
                </div>
              </div>
              <div className="pt-2">
                 <div className="text-[8px] font-mono text-arkhe-muted uppercase mb-1">Decoherence Events</div>
                 <div className="flex gap-1 flex-wrap">
                    <span className="px-1 bg-arkhe-red/20 text-arkhe-red border border-arkhe-red/30 text-[8px] font-mono rounded">B_KLM1</span>
                    <span className="px-1 bg-arkhe-orange/20 text-arkhe-orange border border-arkhe-orange/30 text-[8px] font-mono rounded">W_TIMING</span>
                 </div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
