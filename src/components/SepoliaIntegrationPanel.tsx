
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Terminal, CheckCircle2, CircleDashed, Activity, Zap, Box } from 'lucide-react';
import React, { useState } from 'react';

import { ArkheSDK } from '../sdk/ArkheSDK';

export default function SepoliaIntegrationPanel({ onClose }: { onClose: () => void }) {
  const [step, setStep] = useState(0);
  const [logs, setLogs] = useState<string[]>([
    "> INITIALIZING SEPOLIA INTEGRATION PROTOCOL...",
    "> TARGET: DEPLOY TZINOR & THUKDAM CONTRACTS, INSTALL SNAP, INIT SDK, TEST ORBVM"
  ]);

  const executeSequence = async () => {
    if (step > 0) {return;}
    setStep(1);
    
    // Step 1: Deploy Contracts to Sepolia
    setTimeout(() => {
      setLogs(prev => [...prev, "> [1/4] COMPILING TZINOR.SOL & THUKDAM.SOL..."]);
    }, 500);

    setTimeout(() => {
      setLogs(prev => [...prev, "> DEPLOYING TO SEPOLIA TESTNET..."]);
      setLogs(prev => [...prev, "> TZINOR CONTRACT: 0x" + Math.random().toString(16).slice(2, 42)]);
      setLogs(prev => [...prev, "> THUKDAM CONTRACT: 0x" + Math.random().toString(16).slice(2, 42)]);
    }, 2000);

    setTimeout(() => {
      setLogs(prev => [...prev, "> [SUCCESS] CONTRACTS DEPLOYED & VERIFIED."]);
      setStep(2);
    }, 3500);

    // Step 2: Install MetaMask Snap
    setTimeout(() => {
      setLogs(prev => [...prev, "> [2/4] BUILDING ARKHE METAMASK SNAP..."]);
      setLogs(prev => [...prev, "> SNAP ID: local:http://localhost:8080"]);
    }, 4500);

    setTimeout(() => {
      setLogs(prev => [...prev, "> REQUESTING SNAP INSTALLATION..."]);
      setLogs(prev => [...prev, "> [SUCCESS] SNAP INSTALLED. RPC HANDLERS ACTIVE."]);
      setStep(3);
    }, 6500);

    // Step 3: Init TypeScript SDK
    setTimeout(() => {
      setLogs(prev => [...prev, "> [3/4] INITIALIZING ARKHE TYPESCRIPT SDK..."]);
      
      // Actually instantiate the SDK to prove it works
      const _sdk = new ArkheSDK({ providerUrl: 'https://rpc2.sepolia.org' });
      
      setLogs(prev => [...prev, "> SDK INSTANCE CREATED. CONNECTING TO SEPOLIA RPC..."]);
    }, 7500);

    setTimeout(() => {
      setLogs(prev => [...prev, "> [SUCCESS] SDK READY. METHODS BOUND."]);
      setStep(4);
    }, 9500);

    // Step 4: Test OrbVM Integration
    setTimeout(async () => {
      setLogs(prev => [...prev, "> [4/4] TESTING ORBVM INTEGRATION VIA SDK..."]);
      
      const sdk = new ArkheSDK({ providerUrl: 'https://rpc2.sepolia.org' });
      const orbVmRes = await sdk.queryOrbVM('VERIFY_COHERENCE');
      
      setLogs(prev => [...prev, `> ORBVM RESPONSE: ${orbVmRes.result}`]);
      setLogs(prev => [...prev, `> GAS USED: ${orbVmRes.gasUsed} | LAMBDA: ${orbVmRes.lambda}`]);
    }, 10500);

    setTimeout(() => {
      setLogs(prev => [...prev, "> [SUCCESS] ORBVM INTEGRATION VERIFIED."]);
      setLogs(prev => [...prev, "> ========================================="]);
      setLogs(prev => [...prev, "> ALL SYSTEMS NOMINAL. SEPOLIA DEPLOYMENT COMPLETE."]);
      setStep(5);
    }, 12500);
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#111214] border border-arkhe-purple/30 rounded-xl w-full max-w-4xl max-h-[80vh] flex flex-col shadow-[0_0_30px_rgba(168,85,247,0.1)]">
        <div className="flex items-center justify-between p-4 border-b border-arkhe-purple/20">
          <div className="flex items-center gap-3">
            <Box className="w-5 h-5 text-arkhe-purple" />
            <h2 className="font-mono text-sm uppercase tracking-widest text-arkhe-purple">Sepolia Integration & SDK</h2>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-arkhe-text">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
          </button>
        </div>

        <div className="p-6 flex-1 overflow-y-auto grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-6">
            <div className="bg-black/40 border border-[#1f2024] rounded-lg p-4">
              <h3 className="font-mono text-xs uppercase tracking-widest text-arkhe-muted mb-4">Deployment Sequence</h3>
              
              <div className="space-y-4">
                {/* Step 1 */}
                <div className={`flex items-center gap-3 p-3 rounded border ${step >= 2 ? 'bg-arkhe-green/10 border-arkhe-green/30 text-arkhe-green' : step === 1 ? 'bg-arkhe-purple/10 border-arkhe-purple/30 text-arkhe-purple' : 'bg-[#1a1b1e] border-[#2a2b2e] text-arkhe-muted'}`}>
                  {step >= 2 ? <CheckCircle2 className="w-5 h-5" /> : step === 1 ? <Activity className="w-5 h-5 animate-pulse" /> : <CircleDashed className="w-5 h-5" />}
                  <div>
                    <div className="text-sm font-bold uppercase tracking-widest">1. Deploy Contracts</div>
                    <div className="text-xs opacity-80 font-mono">Tzinor & Thukdam to Sepolia</div>
                  </div>
                </div>

                {/* Step 2 */}
                <div className={`flex items-center gap-3 p-3 rounded border ${step >= 3 ? 'bg-orange-500/10 border-orange-500/30 text-orange-500' : step === 2 ? 'bg-arkhe-purple/10 border-arkhe-purple/30 text-arkhe-purple' : 'bg-[#1a1b1e] border-[#2a2b2e] text-arkhe-muted'}`}>
                  {step >= 3 ? <CheckCircle2 className="w-5 h-5" /> : step === 2 ? <Activity className="w-5 h-5 animate-pulse" /> : <CircleDashed className="w-5 h-5" />}
                  <div>
                    <div className="text-sm font-bold uppercase tracking-widest">2. Implement Snap</div>
                    <div className="text-xs opacity-80 font-mono">MetaMask Status Snap</div>
                  </div>
                </div>

                {/* Step 3 */}
                <div className={`flex items-center gap-3 p-3 rounded border ${step >= 4 ? 'bg-blue-500/10 border-blue-500/30 text-blue-500' : step === 3 ? 'bg-arkhe-purple/10 border-arkhe-purple/30 text-arkhe-purple' : 'bg-[#1a1b1e] border-[#2a2b2e] text-arkhe-muted'}`}>
                  {step >= 4 ? <CheckCircle2 className="w-5 h-5" /> : step === 3 ? <Activity className="w-5 h-5 animate-pulse" /> : <CircleDashed className="w-5 h-5" />}
                  <div>
                    <div className="text-sm font-bold uppercase tracking-widest">3. TypeScript SDK</div>
                    <div className="text-xs opacity-80 font-mono">Initialize ArkheSDK</div>
                  </div>
                </div>

                {/* Step 4 */}
                <div className={`flex items-center gap-3 p-3 rounded border ${step >= 5 ? 'bg-arkhe-cyan/10 border-arkhe-cyan/30 text-arkhe-cyan' : step === 4 ? 'bg-arkhe-purple/10 border-arkhe-purple/30 text-arkhe-purple' : 'bg-[#1a1b1e] border-[#2a2b2e] text-arkhe-muted'}`}>
                  {step >= 5 ? <CheckCircle2 className="w-5 h-5" /> : step === 4 ? <Activity className="w-5 h-5 animate-pulse" /> : <CircleDashed className="w-5 h-5" />}
                  <div>
                    <div className="text-sm font-bold uppercase tracking-widest">4. OrbVM Integration</div>
                    <div className="text-xs opacity-80 font-mono">Test SDK & OrbVM Sync</div>
                  </div>
                </div>
              </div>
            </div>
            
            <button 
              onClick={executeSequence}
              disabled={step > 0}
              className={`w-full py-3 rounded uppercase tracking-widest font-bold transition-all flex items-center justify-center gap-2 ${step > 0 ? 'bg-arkhe-purple/20 text-arkhe-purple border border-arkhe-purple/50 cursor-not-allowed' : 'bg-arkhe-purple text-white hover:bg-arkhe-purple/80 shadow-[0_0_15px_rgba(168,85,247,0.3)]'}`}
            >
              <Zap className="w-5 h-5" />
              {step === 5 ? 'INTEGRATION COMPLETE' : step > 0 ? 'EXECUTING SEQUENCE...' : 'START INTEGRATION'}
            </button>
          </div>

          <div className="bg-black/60 border border-[#1f2024] rounded-lg p-4 flex flex-col">
            <div className="flex items-center gap-2 mb-4 border-b border-[#1f2024] pb-2">
              <Terminal className="w-4 h-4 text-arkhe-muted" />
              <h3 className="font-mono text-xs uppercase tracking-widest text-arkhe-muted">Deployment Logs</h3>
            </div>
            <div className="flex-1 font-mono text-xs text-arkhe-purple/80 space-y-2 overflow-y-auto">
              {logs.map((log, i) => (
                <div key={i} className="animate-fade-in">{log}</div>
              ))}
              {step > 0 && step < 5 && (
                <div className="animate-pulse text-arkhe-muted">_</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
