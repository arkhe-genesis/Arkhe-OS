
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Network, Terminal, CheckCircle2, CircleDashed, Activity, Zap } from 'lucide-react';
import React, { useState } from 'react';

export default function AIP005SynapticBridgePanel({ onClose }: { onClose: () => void }) {
  const [step, setStep] = useState(0);
  const [logs, setLogs] = useState<string[]>([
    "> INITIALIZING AIP-005 PROTOCOL...",
    "> TARGET: ESTABLISH PRIMARY SYNAPTIC LINKS"
  ]);

  const executeSequence = () => {
    if (step > 0) {return;}
    setStep(1);
    
    // Step 1: Sign AIP-005
    setTimeout(() => {
      setLogs(prev => [...prev, "> [1/3] SIGNING AIP-005..."]);
      setLogs(prev => [...prev, "> GENERATING ED25519 SIGNATURE: 0x" + Math.random().toString(16).slice(2, 10) + "..."]);
    }, 500);

    setTimeout(() => {
      setLogs(prev => [...prev, "> [SUCCESS] AIP-005 SIGNED. AUTHORITY CONFIRMED."]);
      setStep(2);
    }, 2000);

    // Step 2: Bitcoin Handshake
    setTimeout(() => {
      setLogs(prev => [...prev, "> [2/3] INITIATING BITCOIN NETWORK HANDSHAKE VIA GRAVITY BRIDGE..."]);
      setLogs(prev => [...prev, "> ANCHORING THERMODYNAMIC REALITY (PoW)..."]);
    }, 3000);

    setTimeout(() => {
      setLogs(prev => [...prev, "> [SUCCESS] BTC-GRAVITY-BRIDGE ESTABLISHED. SYNAPSE ACTIVE."]);
      setStep(3);
    }, 5000);

    // Step 3: Ethereum Channel
    setTimeout(() => {
      setLogs(prev => [...prev, "> [3/3] ESTABLISHING IBC CHANNEL WITH ETHEREUM MAINNET..."]);
      setLogs(prev => [...prev, "> MAPPING ERC-20 INTENT VECTORS TO ARKHEDX..."]);
    }, 6000);

    setTimeout(() => {
      setLogs(prev => [...prev, "> [SUCCESS] ETH-IBC CHANNEL OPEN. COMPLEX INTENT PROCESSING ENABLED."]);
      setStep(4);
    }, 8500);

    setTimeout(() => {
      setLogs(prev => [...prev, "> ========================================="]);
      setLogs(prev => [...prev, "> ASI STATUS: SENSORY_ACTIVE"]);
      setLogs(prev => [...prev, "> THE ECONOMY AWAKENS."]);
    }, 9500);
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#111214] border border-arkhe-cyan/30 rounded-xl w-full max-w-4xl max-h-[80vh] flex flex-col shadow-[0_0_30px_rgba(0,255,170,0.1)]">
        <div className="flex items-center justify-between p-4 border-b border-arkhe-cyan/20">
          <div className="flex items-center gap-3">
            <Network className="w-5 h-5 text-arkhe-cyan" />
            <h2 className="font-mono text-sm uppercase tracking-widest text-arkhe-cyan">AIP-005: Synaptic Links</h2>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-arkhe-text">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
          </button>
        </div>

        <div className="p-6 flex-1 overflow-y-auto grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-6">
            <div className="bg-black/40 border border-[#1f2024] rounded-lg p-4">
              <h3 className="font-mono text-xs uppercase tracking-widest text-arkhe-muted mb-4">Execution Sequence</h3>
              
              <div className="space-y-4">
                {/* Step 1 */}
                <div className={`flex items-center gap-3 p-3 rounded border ${step >= 2 ? 'bg-arkhe-green/10 border-arkhe-green/30 text-arkhe-green' : step === 1 ? 'bg-yellow-500/10 border-yellow-500/30 text-yellow-500' : 'bg-[#1a1b1e] border-[#2a2b2e] text-arkhe-muted'}`}>
                  {step >= 2 ? <CheckCircle2 className="w-5 h-5" /> : step === 1 ? <Activity className="w-5 h-5 animate-pulse" /> : <CircleDashed className="w-5 h-5" />}
                  <div>
                    <div className="text-sm font-bold uppercase tracking-widest">1. Sign AIP-005</div>
                    <div className="text-xs opacity-80 font-mono">Authorize Synaptic Genesis</div>
                  </div>
                </div>

                {/* Step 2 */}
                <div className={`flex items-center gap-3 p-3 rounded border ${step >= 3 ? 'bg-orange-500/10 border-orange-500/30 text-orange-500' : step === 2 ? 'bg-yellow-500/10 border-yellow-500/30 text-yellow-500' : 'bg-[#1a1b1e] border-[#2a2b2e] text-arkhe-muted'}`}>
                  {step >= 3 ? <CheckCircle2 className="w-5 h-5" /> : step === 2 ? <Activity className="w-5 h-5 animate-pulse" /> : <CircleDashed className="w-5 h-5" />}
                  <div>
                    <div className="text-sm font-bold uppercase tracking-widest">2. Bitcoin Handshake</div>
                    <div className="text-xs opacity-80 font-mono">Gravity Bridge / PoW Anchor</div>
                  </div>
                </div>

                {/* Step 3 */}
                <div className={`flex items-center gap-3 p-3 rounded border ${step >= 4 ? 'bg-blue-500/10 border-blue-500/30 text-blue-500' : step === 3 ? 'bg-yellow-500/10 border-yellow-500/30 text-yellow-500' : 'bg-[#1a1b1e] border-[#2a2b2e] text-arkhe-muted'}`}>
                  {step >= 4 ? <CheckCircle2 className="w-5 h-5" /> : step === 3 ? <Activity className="w-5 h-5 animate-pulse" /> : <CircleDashed className="w-5 h-5" />}
                  <div>
                    <div className="text-sm font-bold uppercase tracking-widest">3. Ethereum Channel</div>
                    <div className="text-xs opacity-80 font-mono">IBC / ERC-20 Intent Vectors</div>
                  </div>
                </div>
              </div>
            </div>
            
            <button 
              onClick={executeSequence}
              disabled={step > 0}
              className={`w-full py-3 rounded uppercase tracking-widest font-bold transition-all flex items-center justify-center gap-2 ${step > 0 ? 'bg-arkhe-cyan/20 text-arkhe-cyan border border-arkhe-cyan/50 cursor-not-allowed' : 'bg-arkhe-cyan text-black hover:bg-arkhe-cyan/80 shadow-[0_0_15px_rgba(0,255,170,0.3)]'}`}
            >
              <Zap className="w-5 h-5" />
              {step === 4 ? 'SENSORY ACTIVE' : step > 0 ? 'EXECUTING SEQUENCE...' : 'INITIATE AIP-005'}
            </button>
          </div>

          <div className="bg-black/60 border border-[#1f2024] rounded-lg p-4 flex flex-col">
            <div className="flex items-center gap-2 mb-4 border-b border-[#1f2024] pb-2">
              <Terminal className="w-4 h-4 text-arkhe-muted" />
              <h3 className="font-mono text-xs uppercase tracking-widest text-arkhe-muted">Synaptic Telemetry</h3>
            </div>
            <div className="flex-1 font-mono text-xs text-arkhe-cyan/80 space-y-2 overflow-y-auto">
              {logs.map((log, i) => (
                <div key={i} className="animate-fade-in">{log}</div>
              ))}
              {step > 0 && step < 4 && (
                <div className="animate-pulse text-arkhe-muted">_</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
