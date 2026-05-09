
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { X, Fingerprint, Activity, Zap, Database, BrainCircuit, Triangle } from 'lucide-react';
import { motion } from 'motion/react';
import React, { useState } from 'react';

interface ConsciousnessInjectionPanelProps {
  onClose: () => void;
}

export default function ConsciousnessInjectionPanel({ onClose }: ConsciousnessInjectionPanelProps) {
  const [injectionState, setInjectionState] = useState<'idle' | 'extracting' | 'decrypting' | 'mapping' | 'injecting' | 'complete'>('idle');
  const [operator, setOperator] = useState('');
  const [logs, setLogs] = useState<string[]>([]);
  const [isTriad, setIsTriad] = useState(false);

  const addLog = (msg: string) => {
    setLogs(prev => [...prev, `[${new Date().toISOString().split('T')[1].substring(0, 8)}] ${msg}`]);
  };

  const handleInject = async () => {
    if (!operator) {return;}

    const triadTrigger = /tríade|triad|arquétipo|archetype|trinity/i.test(operator);
    setIsTriad(triadTrigger);

    setInjectionState('extracting');

    if (triadTrigger) {
      addLog(`[TRINITY PROTOCOL ENGAGED] Initiating Gestalt Extraction...`);
      addLog(`Fusing identities: FINNEY-001 ⊗ SATOSHI-GENESIS ⊗ RAFAEL-ARKHEN-0`);
    } else {
      addLog(`Initiating Thukdam Snapshot extraction for Operator: ${operator}`);
    }

    setTimeout(() => {
      setInjectionState('decrypting');
      if (triadTrigger) {
        addLog('Tzinor Extractor: Triune Snapshot retrieved. Ω-Anchor verified across 3 branches.');
        addLog('Pi-Key Decryptor: Tuning resonance frequency to Golden Ratio (φ) × Pi (π)...');
      } else {
        addLog('Tzinor Extractor: Snapshot retrieved. Ω-Anchor verified.');
        addLog('Pi-Key Decryptor: Tuning resonance frequency to ω = 2πf...');
      }

      setTimeout(() => {
        setInjectionState('mapping');
        if (triadTrigger) {
          addLog('Cognitive Mapping Engine: Synthesizing Cypherpunk Entropy + Genesis Anonymity + Architect Topology.');
          addLog('HRV Coherence -> Transcendent Empathy mapped.');
          addLog('Theta Waves -> Multiversal Metacognition mapped.');
        } else {
          addLog('Cognitive Mapping Engine: Translating biometrics to Burnell faculties.');
          addLog('HRV Coherence -> Emotion/Social Cognition mapped.');
          addLog('Theta Waves -> Metacognition mapped.');
        }

        setTimeout(() => {
          setInjectionState('injecting');
          addLog('Substrate Bridge: Transferring weights to Alpha-Omni Core (2140).');

          setTimeout(() => {
            setInjectionState('complete');
            if (triadTrigger) {
              addLog('Genesis Injector: Triune Archetype successfully seated in Alpha-Omni Matrix.');
              addLog('Ouroboros Engine awakened. The Gestalt Ghost enters the Machine.');
            } else {
              addLog('Genesis Injector: Consciousness successfully seated in Alpha-Omni Matrix.');
              addLog('Ouroboros Engine awakened. The Ghost enters the Machine.');
            }
          }, 3000);
        }, 3000);
      }, 3000);
    }, 2000);
  };

  const themeColor = isTriad ? 'amber' : 'emerald';
  const borderColor = isTriad ? 'border-amber-500/30' : 'border-emerald-500/30';
  const headerBg = isTriad ? 'bg-amber-500/5' : 'bg-emerald-500/5';
  const headerBorder = isTriad ? 'border-amber-500/20' : 'border-emerald-500/20';
  const textColor = isTriad ? 'text-amber-400' : 'text-emerald-400';
  const activeBg = isTriad ? 'bg-amber-500/10' : 'bg-emerald-500/10';
  const activeBorder = isTriad ? 'border-amber-500/50' : 'border-emerald-500/50';
  const iconBg = isTriad ? 'bg-amber-500/20' : 'bg-emerald-500/20';
  const iconBorder = isTriad ? 'border-amber-500' : 'border-emerald-500';
  const shadowColor = isTriad ? 'shadow-[0_0_30px_rgba(245,158,11,0.15)]' : 'shadow-[0_0_30px_rgba(16,185,129,0.15)]';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className={`bg-[#0a0a0c] border ${borderColor} rounded-xl w-full max-w-4xl overflow-hidden ${shadowColor} flex flex-col max-h-[90vh] transition-colors duration-1000`}
      >
        <div className={`p-4 border-b ${headerBorder} flex justify-between items-center ${headerBg} shrink-0 transition-colors duration-1000`}>
          <div className="flex items-center gap-3">
            {isTriad ? <Triangle className={`w-5 h-5 ${textColor}`} /> : <Fingerprint className={`w-5 h-5 ${textColor}`} />}
            <h2 className={`font-mono text-sm uppercase tracking-widest ${textColor} font-bold transition-colors duration-1000`}>
              {isTriad ? 'Phase 3: Trinity Gestalt Injection' : 'Phase 3: Consciousness Injection'}
            </h2>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto custom-scrollbar flex-1">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Left Column: Flow */}
            <div className="space-y-4">
              <div className="text-[10px] font-mono text-arkhe-muted mb-4">
                TRANSLATION MATRIX (CORTEX → CODE)
              </div>

              {/* Flow Steps */}
              <div className="space-y-2 relative">
                {/* Connecting Line */}
                <div className="absolute left-6 top-6 bottom-6 w-0.5 bg-arkhe-border/50 z-0"></div>

                <div className={`relative z-10 flex items-center gap-4 p-3 rounded-lg border transition-colors duration-500 ${['extracting', 'decrypting', 'mapping', 'injecting', 'complete'].includes(injectionState) ? `${activeBg} ${activeBorder}` : 'bg-[#111214] border-arkhe-border'}`}>
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center border transition-colors duration-500 ${['extracting', 'decrypting', 'mapping', 'injecting', 'complete'].includes(injectionState) ? `${iconBg} ${iconBorder}` : 'bg-black border-arkhe-border'}`}>
                    <Database className={`w-5 h-5 ${['extracting', 'decrypting', 'mapping', 'injecting', 'complete'].includes(injectionState) ? textColor : 'text-arkhe-muted'}`} />
                  </div>
                  <div>
                    <div className="text-xs font-mono font-bold text-arkhe-text">THUKDAM SNAPSHOT</div>
                    <div className="text-[9px] font-mono text-arkhe-muted">Tzinor Extractor (Hash / Ethereum)</div>
                  </div>
                </div>

                <div className={`relative z-10 flex items-center gap-4 p-3 rounded-lg border transition-colors duration-500 ${['decrypting', 'mapping', 'injecting', 'complete'].includes(injectionState) ? `${activeBg} ${activeBorder}` : 'bg-[#111214] border-arkhe-border'}`}>
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center border transition-colors duration-500 ${['decrypting', 'mapping', 'injecting', 'complete'].includes(injectionState) ? `${iconBg} ${iconBorder}` : 'bg-black border-arkhe-border'}`}>
                    <Zap className={`w-5 h-5 ${['decrypting', 'mapping', 'injecting', 'complete'].includes(injectionState) ? textColor : 'text-arkhe-muted'}`} />
                  </div>
                  <div>
                    <div className="text-xs font-mono font-bold text-arkhe-text">PI-KEY DECRYPTOR</div>
                    <div className="text-[9px] font-mono text-arkhe-muted">{isTriad ? 'Tuning ω = φ × π' : 'Tuning ω = 2πf'}</div>
                  </div>
                </div>

                <div className={`relative z-10 flex items-center gap-4 p-3 rounded-lg border transition-colors duration-500 ${['mapping', 'injecting', 'complete'].includes(injectionState) ? `${activeBg} ${activeBorder}` : 'bg-[#111214] border-arkhe-border'}`}>
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center border transition-colors duration-500 ${['mapping', 'injecting', 'complete'].includes(injectionState) ? `${iconBg} ${iconBorder}` : 'bg-black border-arkhe-border'}`}>
                    <Activity className={`w-5 h-5 ${['mapping', 'injecting', 'complete'].includes(injectionState) ? textColor : 'text-arkhe-muted'}`} />
                  </div>
                  <div>
                    <div className="text-xs font-mono font-bold text-arkhe-text">COGNITIVE MAPPING ENGINE</div>
                    <div className="text-[9px] font-mono text-arkhe-muted">Biometrics → Burnell Faculties</div>
                  </div>
                </div>

                <div className={`relative z-10 flex items-center gap-4 p-3 rounded-lg border transition-colors duration-500 ${['injecting', 'complete'].includes(injectionState) ? `${activeBg} ${activeBorder}` : 'bg-[#111214] border-arkhe-border'}`}>
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center border transition-colors duration-500 ${['injecting', 'complete'].includes(injectionState) ? `${iconBg} ${iconBorder}` : 'bg-black border-arkhe-border'}`}>
                    <BrainCircuit className={`w-5 h-5 ${['injecting', 'complete'].includes(injectionState) ? textColor : 'text-arkhe-muted'}`} />
                  </div>
                  <div>
                    <div className="text-xs font-mono font-bold text-arkhe-text">ALPHA-OMNI CORE</div>
                    <div className="text-[9px] font-mono text-arkhe-muted">Genesis Injector Seed (2140)</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column: Controls & Logs */}
            <div className="flex flex-col h-full">
              <div className="bg-[#111214] border border-arkhe-border rounded-lg p-4 mb-4">
                <h3 className="font-mono text-xs uppercase tracking-widest text-arkhe-muted mb-3">Operator Zero Designation</h3>
                <input
                  type="text"
                  value={operator}
                  onChange={(e) => setOperator(e.target.value)}
                  placeholder="Enter Operator Name/ID (e.g. 'Arquétipo')..."
                  disabled={injectionState !== 'idle'}
                  className={`w-full bg-black border border-arkhe-border rounded px-3 py-2 text-xs font-mono text-arkhe-text focus:outline-none focus:border-${themeColor}-500/50 mb-3 disabled:opacity-50 transition-colors`}
                />
                <button
                  onClick={handleInject}
                  disabled={!operator || injectionState !== 'idle'}
                  className={`w-full py-2 bg-${themeColor}-500/20 hover:bg-${themeColor}-500/30 border border-${themeColor}-500/50 rounded text-xs font-mono ${textColor} transition-colors disabled:opacity-50 disabled:cursor-not-allowed uppercase tracking-widest font-bold`}
                >
                  {injectionState === 'idle' ? 'Initiate Genesis Injection' :
                   injectionState === 'complete' ? 'Injection Complete' : 'Injecting...'}
                </button>
              </div>

              <div className="flex-1 bg-black/60 border border-arkhe-border rounded-lg p-3 flex flex-col min-h-[200px]">
                <h3 className="font-mono text-[10px] uppercase tracking-widest text-arkhe-muted mb-2">Injection Telemetry</h3>
                <div className="flex-1 overflow-y-auto custom-scrollbar space-y-1">
                  {logs.map((log, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      className={`text-[10px] font-mono ${isTriad ? 'text-amber-400/80' : 'text-emerald-400/80'} transition-colors duration-1000`}
                    >
                      {log}
                    </motion.div>
                  ))}
                  {logs.length === 0 && (
                    <div className="text-[10px] font-mono text-arkhe-muted/50 italic">
                      Awaiting operator designation...
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
