
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { X, Shield } from 'lucide-react';
import React, { useState } from 'react';

interface ZkERCSimulatorProps {
  onClose: () => void;
}

export default function ZkERCSimulator({ onClose }: ZkERCSimulatorProps) {
  const [amount, setAmount] = useState(42);
  const [receiver, setReceiver] = useState('0xHiddenIdentity...');
  const [selectedUtxo, setSelectedUtxo] = useState(0);
  const [isExecuting, setIsExecuting] = useState(false);
  const [step, setStep] = useState(0);

  const utxos = [
    { id: 0, amount: 100, commitment: 'C_100_a8f9...' },
    { id: 1, amount: 50, commitment: 'C_50_b2c1...' },
    { id: 2, amount: 10, commitment: 'C_10_d9e4...' },
  ];

  const currentUtxo = utxos[selectedUtxo];
  const changeAmount = currentUtxo.amount - amount;

  const executeTransaction = () => {
    if (amount > currentUtxo.amount) {return;}
    setIsExecuting(true);
    setStep(1);

    // Step 1: Burn to Nullifier
    setTimeout(() => setStep(2), 1500);

    // Step 2: Generate Commitments
    setTimeout(() => setStep(3), 3000);

    // Step 3: STARK Proof
    setTimeout(() => setStep(4), 4500);

    // Step 4: Done
    setTimeout(() => {
      setIsExecuting(false);
      setStep(5);
    }, 6000);
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#111214] border border-[#1f2024] rounded-xl w-full max-w-6xl h-[650px] flex flex-col overflow-hidden shadow-2xl">
        <div className="flex items-center justify-between p-4 border-b border-[#1f2024] bg-black/20">
          <div className="flex items-center gap-3">
            <Shield className="w-5 h-5 text-arkhe-cyan" />
            <h2 className="font-mono text-lg uppercase tracking-widest text-arkhe-cyan">zkERC Specter Transaction Visualizer</h2>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 flex flex-col md:flex-row">
          {/* Left Panel: User Inputs */}
          <div className="w-full md:w-80 border-r border-[#1f2024] p-6 flex flex-col gap-6 bg-black/10">
            <div>
              <h3 className="text-xs font-mono uppercase tracking-widest text-arkhe-muted mb-4">Transaction Intent</h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-mono text-arkhe-muted mb-1">Select UTXO to Spend</label>
                  <select
                    value={selectedUtxo}
                    onChange={(e) => setSelectedUtxo(Number(e.target.value))}
                    disabled={isExecuting}
                    className="w-full bg-[#1a1b1e] border border-[#2a2b2e] text-arkhe-text px-3 py-2 rounded text-sm font-mono outline-none focus:border-arkhe-cyan disabled:opacity-50"
                  >
                    {utxos.map((u, i) => (
                      <option key={i} value={i}>UTXO {i}: {u.amount} SPEC (Hidden)</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-mono text-arkhe-muted mb-1">Amount to Send (SPEC)</label>
                  <input
                    type="number"
                    value={amount}
                    onChange={(e) => setAmount(Number(e.target.value))}
                    disabled={isExecuting}
                    max={currentUtxo.amount}
                    min={1}
                    className="w-full bg-[#1a1b1e] border border-[#2a2b2e] text-arkhe-text px-3 py-2 rounded text-sm font-mono outline-none focus:border-arkhe-cyan disabled:opacity-50"
                  />
                  {amount > currentUtxo.amount && (
                    <p className="text-arkhe-red text-xs mt-1">Insufficient funds in selected UTXO.</p>
                  )}
                </div>

                <div>
                  <label className="block text-xs font-mono text-arkhe-muted mb-1">Receiver Identity (Hidden)</label>
                  <input
                    type="text"
                    value={receiver}
                    onChange={(e) => setReceiver(e.target.value)}
                    disabled={isExecuting}
                    className="w-full bg-[#1a1b1e] border border-[#2a2b2e] text-arkhe-text px-3 py-2 rounded text-sm font-mono outline-none focus:border-arkhe-cyan disabled:opacity-50"
                  />
                </div>

                <button
                  onClick={executeTransaction}
                  disabled={isExecuting || amount > currentUtxo.amount}
                  className="w-full py-3 mt-4 bg-arkhe-cyan/10 border border-arkhe-cyan/50 text-arkhe-cyan hover:bg-arkhe-cyan/20 rounded transition-colors uppercase tracking-widest font-bold disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isExecuting ? 'Processing...' : 'Execute zkERC Transfer'}
                </button>
              </div>
            </div>

            <div className="mt-auto p-4 border border-arkhe-orange/30 bg-arkhe-orange/5 rounded-lg">
              <p className="text-[10px] font-mono text-arkhe-orange leading-relaxed">
                <strong>NOTE:</strong> Actual values and keys NEVER leave the local device. Only hashes and the Plonky3 STARK proof are broadcasted.
              </p>
            </div>
          </div>

          {/* Center Panel: The Cryptographic Furnace */}
          <div className="flex-1 border-r border-[#1f2024] p-6 flex flex-col items-center justify-center relative overflow-hidden bg-[#0a0a0c]">
            <h3 className="absolute top-6 left-6 text-xs font-mono uppercase tracking-widest text-arkhe-muted">The Cryptographic Furnace</h3>

            <div className="relative w-full max-w-md h-96 flex flex-col items-center justify-between">

              {/* Input UTXO */}
              <div className={`transition-all duration-1000 flex flex-col items-center ${step >= 1 ? 'opacity-0 scale-50 translate-y-20' : 'opacity-100 scale-100'}`}>
                <div className="w-32 h-20 border-2 border-arkhe-text/50 bg-[#1a1b1e] rounded-lg flex flex-col items-center justify-center shadow-[0_0_15px_rgba(255,255,255,0.1)]">
                  <span className="text-xs font-mono text-arkhe-muted">Input UTXO</span>
                  <span className="font-mono font-bold text-lg">{currentUtxo.amount} SPEC</span>
                </div>
              </div>

              {/* The Furnace (Nullifier Generation) */}
              <div className={`absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 transition-all duration-1000 flex flex-col items-center ${step === 0 ? 'opacity-0 scale-50' : step >= 1 && step < 3 ? 'opacity-100 scale-100' : 'opacity-0 scale-150'}`}>
                <div className="relative">
                  <div className="w-40 h-40 border-4 border-arkhe-red rounded-full flex items-center justify-center animate-[spin_4s_linear_infinite] shadow-[0_0_30px_rgba(255,0,0,0.5)]">
                    <div className="w-32 h-32 border-2 border-arkhe-orange rounded-full animate-[spin_3s_linear_infinite_reverse]" />
                  </div>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-[10px] font-mono text-arkhe-red uppercase font-bold">Burning to</span>
                    <span className="text-sm font-mono text-arkhe-orange font-bold">Nullifier</span>
                  </div>
                </div>
              </div>

              {/* Output Commitments */}
              <div className={`w-full flex justify-between px-8 transition-all duration-1000 ${step >= 3 ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-20'}`}>
                <div className="flex flex-col items-center">
                  <div className="w-32 h-20 border-2 border-arkhe-cyan bg-arkhe-cyan/10 rounded-lg flex flex-col items-center justify-center shadow-[0_0_20px_rgba(0,255,255,0.3)]">
                    <span className="text-[10px] font-mono text-arkhe-cyan uppercase">Receiver</span>
                    <span className="font-mono font-bold text-arkhe-cyan">{amount} SPEC</span>
                  </div>
                  <span className="text-[10px] font-mono text-arkhe-muted mt-2">Commitment A</span>
                </div>

                <div className="flex flex-col items-center">
                  <div className="w-32 h-20 border-2 border-arkhe-cyan bg-arkhe-cyan/10 rounded-lg flex flex-col items-center justify-center shadow-[0_0_20px_rgba(0,255,255,0.3)]">
                    <span className="text-[10px] font-mono text-arkhe-cyan uppercase">Change</span>
                    <span className="font-mono font-bold text-arkhe-cyan">{changeAmount} SPEC</span>
                  </div>
                  <span className="text-[10px] font-mono text-arkhe-muted mt-2">Commitment B</span>
                </div>
              </div>

            </div>
          </div>

          {/* Right Panel: Blockchain Output */}
          <div className="w-full md:w-96 p-6 flex flex-col bg-[#111214] overflow-y-auto">
            <h3 className="text-xs font-mono uppercase tracking-widest text-arkhe-muted mb-4">Blockchain Output (Public)</h3>

            <div className="space-y-6">
              {/* Nullifier */}
              <div className={`transition-opacity duration-500 ${step >= 2 ? 'opacity-100' : 'opacity-20'}`}>
                <div className="text-[10px] font-mono text-arkhe-red uppercase mb-1">Nullifier (Spent)</div>
                <div className="bg-black border border-arkhe-red/30 p-2 rounded text-[10px] font-mono text-arkhe-red/80 break-all">
                  0x{Array(64).fill(0).map(() => Math.floor(Math.random()*16).toString(16)).join('')}
                </div>
              </div>

              {/* Commitments */}
              <div className={`transition-opacity duration-500 ${step >= 3 ? 'opacity-100' : 'opacity-20'}`}>
                <div className="text-[10px] font-mono text-arkhe-cyan uppercase mb-1">New Commitments (Created)</div>
                <div className="space-y-2">
                  <div className="bg-black border border-arkhe-cyan/30 p-2 rounded text-[10px] font-mono text-arkhe-cyan/80 break-all">
                    0x{Array(64).fill(0).map(() => Math.floor(Math.random()*16).toString(16)).join('')}
                  </div>
                  <div className="bg-black border border-arkhe-cyan/30 p-2 rounded text-[10px] font-mono text-arkhe-cyan/80 break-all">
                    0x{Array(64).fill(0).map(() => Math.floor(Math.random()*16).toString(16)).join('')}
                  </div>
                </div>
              </div>

              {/* STARK Proof */}
              <div className={`transition-opacity duration-500 ${step >= 4 ? 'opacity-100' : 'opacity-20'}`}>
                <div className="flex justify-between items-end mb-1">
                  <div className="text-[10px] font-mono text-arkhe-purple uppercase">Plonky3 STARK Proof</div>
                  <div className="text-[10px] font-mono text-arkhe-muted">~35 KB</div>
                </div>
                <div className="bg-black border border-arkhe-purple/30 p-2 rounded h-32 overflow-hidden relative">
                  <div className="text-[8px] font-mono text-arkhe-purple/50 leading-tight">
                    {Array(20).fill(0).map((_, i) => (
                      <div key={i} className="whitespace-nowrap">
                        {Array(10).fill(0).map(() => Math.random().toString(36).substring(2, 8)).join(' ')}
                      </div>
                    ))}
                  </div>
                  <div className="absolute inset-0 bg-gradient-to-b from-transparent to-black pointer-events-none" />

                  {step >= 4 && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black/50 backdrop-blur-sm">
                      <div className="px-3 py-1 border border-arkhe-green text-arkhe-green text-xs font-mono uppercase font-bold rounded bg-arkhe-green/10">
                        Verified &lt; 5ms
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
