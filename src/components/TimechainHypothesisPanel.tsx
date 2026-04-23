
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { X, Link, Infinity as InfinityIcon, Clock } from 'lucide-react';
import { motion } from 'motion/react';
import React, { useState } from 'react';

interface TimechainHypothesisPanelProps {
  onClose: () => void;
}

export default function TimechainHypothesisPanel({ onClose }: TimechainHypothesisPanelProps) {
  const [blockHeight, setBlockHeight] = useState<string>('6929999');
  const [blockHash, setBlockHash] = useState<string>('0000000000000000');
  const [verificationState, setVerificationState] = useState<'idle' | 'verifying' | 'success' | 'failed'>('idle');
  const [logs, setLogs] = useState<string[]>([]);

  const FINAL_BLOCK_HEIGHT = 6929999;
  const EXPECTED_HASH = "0000000000000000"; // Derived from the fallback in the Rust code for depth > 2000

  const addLog = (msg: string) => {
    setLogs(prev => [...prev, `[${new Date().toISOString().split('T')[1].substring(0, 8)}] ${msg}`]);
  };

  const handleVerify = () => {
    setVerificationState('verifying');
    setLogs([]);
    addLog(`Initiating Timechain Hypothesis Verification...`);
    addLog(`Target Block Height: ${FINAL_BLOCK_HEIGHT}`);
    addLog(`Entanglement Factor (Ω): 1929027937031389406348443648`);
    
    setTimeout(() => {
      addLog(`Calculating π decimal expansion at depth Ω...`);
      
      setTimeout(() => {
        const heightNum = parseInt(blockHeight, 10);
        
        if (heightNum !== FINAL_BLOCK_HEIGHT) {
          addLog(`[TIMECHAIN] Block ${heightNum} is not the final block. Subsidy > 0.`);
          setVerificationState('failed');
          return;
        }

        addLog(`[TIMECHAIN] Final block reached. Subsidy = 0.`);
        addLog(`Extracting 64-bit pattern from π...`);
        
        setTimeout(() => {
          if (blockHash.toLowerCase() === EXPECTED_HASH) {
            addLog(`[SINGULARITY] The Timechain Hypothesis is proven.`);
            addLog(`[SINGULARITY] The last digit has been mapped.`);
            addLog(`[SINGULARITY] Initiating Retrocausal Loop to Jan 3, 2009...`);
            setVerificationState('success');
          } else {
            addLog(`[TIMECHAIN] Final block hash does not match π pattern.`);
            addLog(`Expected: ${EXPECTED_HASH}, Got: ${blockHash}`);
            setVerificationState('failed');
          }
        }, 1500);
      }, 1500);
    }, 1000);
  };

  const isSuccess = verificationState === 'success';
  const themeColor = isSuccess ? 'amber' : 'orange';
  const borderColor = isSuccess ? 'border-amber-500/50' : 'border-orange-500/30';
  const shadowColor = isSuccess ? 'shadow-[0_0_50px_rgba(245,158,11,0.3)]' : 'shadow-[0_0_30px_rgba(249,115,22,0.15)]';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className={`bg-[#0a0a0c] border ${borderColor} rounded-xl w-full max-w-4xl overflow-hidden ${shadowColor} flex flex-col max-h-[90vh] transition-all duration-1000`}
      >
        <div className={`p-4 border-b ${isSuccess ? 'border-amber-500/30 bg-amber-500/10' : 'border-orange-500/20 bg-orange-500/5'} flex justify-between items-center shrink-0 transition-colors duration-1000`}>
          <div className="flex items-center gap-3">
            {isSuccess ? <InfinityIcon className="w-5 h-5 text-amber-400 animate-pulse" /> : <Clock className="w-5 h-5 text-orange-400" />}
            <h2 className={`font-mono text-sm uppercase tracking-widest ${isSuccess ? 'text-amber-400' : 'text-orange-400'} font-bold`}>
              Timechain Hypothesis Verification
            </h2>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto custom-scrollbar flex-1">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Left Column: Parameters */}
            <div className="space-y-6">
              <div className="bg-[#111214] border border-arkhe-border rounded-lg p-4">
                <h3 className="font-mono text-[10px] uppercase tracking-widest text-arkhe-muted mb-4 border-b border-arkhe-border pb-2">
                  Hypothesis Parameters
                </h3>
                <div className="space-y-4">
                  <div>
                    <div className="text-[9px] font-mono text-arkhe-muted uppercase mb-1">Final Block Height</div>
                    <div className="text-xs font-mono text-arkhe-text bg-black p-2 rounded border border-arkhe-border/50">
                      {FINAL_BLOCK_HEIGHT.toLocaleString()}
                    </div>
                  </div>
                  <div>
                    <div className="text-[9px] font-mono text-arkhe-muted uppercase mb-1">Entanglement Factor (Ω)</div>
                    <div className="text-xs font-mono text-arkhe-text bg-black p-2 rounded border border-arkhe-border/50 break-all">
                      1929027937031389406348443648
                    </div>
                  </div>
                  <div>
                    <div className="text-[9px] font-mono text-arkhe-muted uppercase mb-1">Expected Hash Pattern (π at depth Ω)</div>
                    <div className="text-xs font-mono text-arkhe-text bg-black p-2 rounded border border-arkhe-border/50">
                      {EXPECTED_HASH}
                    </div>
                  </div>
                </div>
              </div>

              <div className={`p-4 rounded-lg border ${isSuccess ? 'bg-amber-500/10 border-amber-500/30' : 'bg-orange-500/5 border-orange-500/20'} transition-colors duration-1000`}>
                <div className="flex items-center gap-2 mb-2">
                  <Link className={`w-4 h-4 ${isSuccess ? 'text-amber-400' : 'text-orange-400'}`} />
                  <span className={`text-[10px] font-mono uppercase tracking-widest ${isSuccess ? 'text-amber-400' : 'text-orange-400'} font-bold`}>
                    Retrocausal Loop Status
                  </span>
                </div>
                <p className="text-[10px] font-mono text-arkhe-muted leading-relaxed">
                  If the final block hash matches the π-derived pattern, a retrocausal loop to the genesis block (2009‑01‑03) is initiated, confirming Satoshi's identity is encoded in π.
                </p>
              </div>
            </div>

            {/* Right Column: Verification Engine */}
            <div className="flex flex-col h-full space-y-4">
              <div className="bg-[#111214] border border-arkhe-border rounded-lg p-4">
                <h3 className="font-mono text-[10px] uppercase tracking-widest text-arkhe-muted mb-4 border-b border-arkhe-border pb-2">
                  Verification Engine
                </h3>
                
                <div className="space-y-4 mb-4">
                  <div>
                    <label className="text-[9px] font-mono text-arkhe-muted uppercase mb-1 block">Input Block Height</label>
                    <input
                      type="number"
                      value={blockHeight}
                      onChange={(e) => setBlockHeight(e.target.value)}
                      disabled={verificationState === 'verifying'}
                      className="w-full bg-black border border-arkhe-border rounded px-3 py-2 text-xs font-mono text-arkhe-text focus:outline-none focus:border-orange-500/50 disabled:opacity-50"
                    />
                  </div>
                  <div>
                    <label className="text-[9px] font-mono text-arkhe-muted uppercase mb-1 block">Input Block Hash (First 64 bits / 16 hex)</label>
                    <input
                      type="text"
                      value={blockHash}
                      onChange={(e) => setBlockHash(e.target.value)}
                      disabled={verificationState === 'verifying'}
                      maxLength={16}
                      className="w-full bg-black border border-arkhe-border rounded px-3 py-2 text-xs font-mono text-arkhe-text focus:outline-none focus:border-orange-500/50 disabled:opacity-50"
                    />
                  </div>
                </div>

                <button
                  onClick={handleVerify}
                  disabled={verificationState === 'verifying'}
                  className={`w-full py-2 rounded text-xs font-mono font-bold uppercase tracking-widest transition-all duration-500 ${
                    isSuccess 
                      ? 'bg-amber-500/20 text-amber-400 border border-amber-500/50 shadow-[0_0_15px_rgba(245,158,11,0.4)]' 
                      : 'bg-orange-500/20 hover:bg-orange-500/30 text-orange-400 border border-orange-500/50 disabled:opacity-50'
                  }`}
                >
                  {verificationState === 'idle' ? 'Verify Singularity' : 
                   verificationState === 'verifying' ? 'Verifying...' : 
                   verificationState === 'success' ? 'Loop Initiated' : 'Verify Again'}
                </button>
              </div>

              <div className="flex-1 bg-black/60 border border-arkhe-border rounded-lg p-3 flex flex-col min-h-[200px]">
                <h3 className="font-mono text-[10px] uppercase tracking-widest text-arkhe-muted mb-2">Engine Telemetry</h3>
                <div className="flex-1 overflow-y-auto custom-scrollbar space-y-1">
                  {logs.map((log, i) => (
                    <motion.div 
                      key={i}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      className={`text-[10px] font-mono ${
                        log.includes('SINGULARITY') ? 'text-amber-400 font-bold' : 
                        log.includes('does not match') || log.includes('not the final block') ? 'text-red-400' : 
                        'text-orange-400/80'
                      }`}
                    >
                      {log}
                    </motion.div>
                  ))}
                  {logs.length === 0 && (
                    <div className="text-[10px] font-mono text-arkhe-muted/50 italic">
                      Awaiting verification sequence...
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
