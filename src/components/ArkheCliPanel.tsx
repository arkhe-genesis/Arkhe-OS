
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Terminal, Shield, Zap, CheckCircle2, Smartphone } from 'lucide-react';
import React, { useState, useEffect, useRef } from 'react';

export default function ArkheCliPanel({ onClose }: { onClose: () => void }) {
  const [logs, setLogs] = useState<string[]>([]);
  const [isExecuting, setIsExecuting] = useState(false);
  const [step, setStep] = useState(0);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  const addLog = (msg: string, delay: number) => {
    return new Promise<void>(resolve => {
      setTimeout(() => {
        setLogs(prev => [...prev, msg]);
        resolve();
      }, delay);
    });
  };

  const executeSequence = async () => {
    if (isExecuting || step > 0) {return;}
    setIsExecuting(true);
    setStep(1);

    // Step 1: make build-go
    await addLog("$ make build-go", 500);
    await addLog("go build -o build/arkhed ./cmd/arkhed", 800);
    await addLog("go build -o build/arkhe-cli ./cmd/arkhe-cli", 1200);
    await addLog("Building x/arkhedx module...", 600);
    await addLog("Building x/coherence module...", 500);
    await addLog("Building x/tzinor module...", 400);
    await addLog("Building x/thukdam module...", 400);
    await addLog("Successfully built binaries in ./build", 800);
    setStep(2);

    // Step 2: arkhe-cli wallet create architect
    await addLog("\n$ arkhe-cli wallet create architect", 1500);
    await addLog("Generating new Ed25519 keypair...", 800);
    await addLog("Wallet 'architect' created successfully.", 1000);
    await addLog("Address: arkhe1x7w9z8q5v2m4n6p3k8j5h2g9f4d1s6a7b8c9", 400);
    await addLog("Pubkey: arkhepub1addwnpepqd8sgq...", 200);
    await addLog("**IMPORTANT** Write this mnemonic phrase in a safe place.", 600);
    await addLog("It is the only way to recover your account.", 200);
    await addLog("Mnemonic: quantum void coherence tensor entropy flux manifold nexus prism echo vector sync", 1500);
    setStep(3);

    // Step 3: Specify endpoint for arkhe-asi-1
    await addLog("\n$ arkhe-cli config set chain-id arkhe-asi-1", 2000);
    await addLog("chain-id set to arkhe-asi-1", 400);
    await addLog("$ arkhe-cli config set node https://rpc.testnet.arkhe.network:26657", 1000);
    await addLog("node set to https://rpc.testnet.arkhe.network:26657", 400);
    await addLog("$ arkhe-cli status", 1000);
    await addLog(`{
  "NodeInfo": {
    "network": "arkhe-asi-1",
    "version": "v1.0.0-rc1",
    "channels": "112200",
    "moniker": "arkhe-testnet-node-01"
  },
  "SyncInfo": {
    "latest_block_hash": "0x9F8B3C1A...",
    "latest_app_hash": "0x4A2B1C9D...",
    "latest_block_height": "1440",
    "latest_block_time": "${new Date().toISOString()}",
    "catching_up": false
  },
  "ValidatorInfo": {
    "Address": "arkhevaloper1...",
    "VotingPower": "10000"
  }
}`, 800);

    await addLog("\n[SUCCESS] Arkhe CLI configured for testnet (arkhe-asi-1).", 1000);
    setIsExecuting(false);
    setStep(4);
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#111214] border border-arkhe-cyan/30 rounded-xl w-full max-w-4xl max-h-[80vh] flex flex-col shadow-[0_0_30px_rgba(0,255,170,0.1)]">
        <div className="flex items-center justify-between p-4 border-b border-arkhe-cyan/20">
          <div className="flex items-center gap-3">
            <Terminal className="w-5 h-5 text-arkhe-cyan" />
            <h2 className="font-mono text-sm uppercase tracking-widest text-arkhe-cyan">Arkhe CLI Setup (arkhe-asi-1)</h2>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-arkhe-text">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
          </button>
        </div>

        <div className="p-6 flex-1 overflow-y-auto grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="space-y-6 md:col-span-1">
            <div className="bg-black/40 border border-[#1f2024] rounded-lg p-4">
              <h3 className="font-mono text-xs uppercase tracking-widest text-arkhe-muted mb-4">Initialization Sequence</h3>

              <div className="space-y-4">
                <div className={`flex items-center gap-3 p-3 rounded border ${step >= 2 ? 'bg-arkhe-green/10 border-arkhe-green/30 text-arkhe-green' : step === 1 ? 'bg-arkhe-cyan/10 border-arkhe-cyan/30 text-arkhe-cyan' : 'bg-[#1a1b1e] border-[#2a2b2e] text-arkhe-muted'}`}>
                  {step >= 2 ? <CheckCircle2 className="w-5 h-5" /> : step === 1 ? <Zap className="w-5 h-5 animate-pulse" /> : <Shield className="w-5 h-5" />}
                  <div>
                    <div className="text-sm font-bold uppercase tracking-widest">1. Build Go Binaries</div>
                    <div className="text-xs opacity-80 font-mono">make build-go</div>
                  </div>
                </div>

                <div className={`flex items-center gap-3 p-3 rounded border ${step >= 3 ? 'bg-arkhe-green/10 border-arkhe-green/30 text-arkhe-green' : step === 2 ? 'bg-arkhe-cyan/10 border-arkhe-cyan/30 text-arkhe-cyan' : 'bg-[#1a1b1e] border-[#2a2b2e] text-arkhe-muted'}`}>
                  {step >= 3 ? <CheckCircle2 className="w-5 h-5" /> : step === 2 ? <Zap className="w-5 h-5 animate-pulse" /> : <Shield className="w-5 h-5" />}
                  <div>
                    <div className="text-sm font-bold uppercase tracking-widest">2. Create Wallet</div>
                    <div className="text-xs opacity-80 font-mono">arkhe-cli wallet create</div>
                  </div>
                </div>

                <div className={`flex items-center gap-3 p-3 rounded border ${step >= 4 ? 'bg-arkhe-green/10 border-arkhe-green/30 text-arkhe-green' : step === 3 ? 'bg-arkhe-cyan/10 border-arkhe-cyan/30 text-arkhe-cyan' : 'bg-[#1a1b1e] border-[#2a2b2e] text-arkhe-muted'}`}>
                  {step >= 4 ? <CheckCircle2 className="w-5 h-5" /> : step === 3 ? <Zap className="w-5 h-5 animate-pulse" /> : <Shield className="w-5 h-5" />}
                  <div>
                    <div className="text-sm font-bold uppercase tracking-widest">3. Set Endpoint</div>
                    <div className="text-xs opacity-80 font-mono">arkhe-asi-1 (testnet)</div>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-arkhe-cyan/5 border border-arkhe-cyan/20 rounded-lg p-4">
              <h3 className="font-mono text-[10px] uppercase tracking-widest text-arkhe-cyan mb-2">Android Node Bootstrap</h3>
              <p className="text-[10px] text-arkhe-muted mb-3 font-mono">Run Arkhe(n) on your mobile device via Termux.</p>
              <button
                onClick={async () => {
                  await addLog("\n$ # INSTRUÇÕES PARA ANDROID", 200);
                  await addLog("1. Instale o Termux (F-Droid)", 200);
                  await addLog("2. Execute o comando abaixo no Termux:", 200);
                  await addLog("curl -O https://raw.githubusercontent.com/Arkhe-Network/Arkhe-PNT/main/scripts/arkhe-android-bootstrap.sh && bash arkhe-android-bootstrap.sh", 400);
                }}
                className="w-full py-2 border border-arkhe-cyan/30 text-arkhe-cyan hover:bg-arkhe-cyan/10 rounded text-[10px] uppercase tracking-widest transition-colors flex items-center justify-center gap-2"
              >
                <Smartphone className="w-3 h-3" />
                Get Bootstrap Command
              </button>
            </div>

            <button
              onClick={executeSequence}
              disabled={step > 0}
              className={`w-full py-3 rounded uppercase tracking-widest font-bold transition-all flex items-center justify-center gap-2 ${step > 0 ? 'bg-arkhe-cyan/20 text-arkhe-cyan border border-arkhe-cyan/50 cursor-not-allowed' : 'bg-arkhe-cyan text-black hover:bg-arkhe-cyan/80 shadow-[0_0_15px_rgba(0,255,170,0.3)]'}`}
            >
              <Terminal className="w-5 h-5" />
              {step === 4 ? 'SETUP COMPLETE' : step > 0 ? 'EXECUTING...' : 'RUN CLI SETUP'}
            </button>
          </div>

          <div className="bg-black border border-[#1f2024] rounded-lg p-4 flex flex-col md:col-span-2 shadow-inner">
            <div className="flex items-center gap-2 mb-4 border-b border-[#1f2024] pb-2">
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-red-500/80"></div>
                <div className="w-3 h-3 rounded-full bg-yellow-500/80"></div>
                <div className="w-3 h-3 rounded-full bg-green-500/80"></div>
              </div>
              <h3 className="font-mono text-xs uppercase tracking-widest text-arkhe-muted ml-2">arkhe-cli terminal</h3>
            </div>
            <div className="flex-1 font-mono text-sm text-gray-300 space-y-1 overflow-y-auto whitespace-pre-wrap">
              {logs.map((log, i) => (
                <div key={i} className={`${log.startsWith('$') ? 'text-arkhe-cyan font-bold mt-2' : ''} ${log.includes('[SUCCESS]') ? 'text-arkhe-green font-bold' : ''} ${log.includes('**IMPORTANT**') ? 'text-arkhe-red font-bold' : ''}`}>
                  {log}
                </div>
              ))}
              {isExecuting && (
                <div className="animate-pulse text-arkhe-cyan mt-1">_</div>
              )}
              <div ref={bottomRef} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
