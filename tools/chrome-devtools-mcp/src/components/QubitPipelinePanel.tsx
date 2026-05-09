
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Cpu, Zap, Activity, BarChart3, Binary, Shield, X, Microscope } from 'lucide-react';
import { motion } from 'motion/react';
import React, { useState, useEffect } from 'react';

export default function QubitPipelinePanel({ onClose }: { onClose: () => void }) {
  const step = 3;
  const [metrics, setMetrics] = useState({
    t2_star: 45.2,
    t2: 120.5,
    gate_fidelity: 0.9992,
    snr: 42.1
  });

  useEffect(() => {
    const interval = setInterval(() => {
      setMetrics(prev => ({
        ...prev,
        gate_fidelity: 0.9990 + Math.random() * 0.0009,
        snr: 42.0 + Math.random() * 0.5
      }));
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const steps = [
    { id: 1, name: 'Charge Sensor Tuning', icon: <Microscope className="w-4 h-4" />, status: 'Complete' },
    { id: 2, name: 'Few-Electron Mapping', icon: <Binary className="w-4 h-4" />, status: 'Complete' },
    { id: 3, name: 'Sweet Spot Localization', icon: <Zap className="w-4 h-4" />, status: 'Active' },
    { id: 4, name: 'Coherence Characterization', icon: <Activity className="w-4 h-4" />, status: 'Pending' },
    { id: 5, name: 'Gate Calibration', icon: <Shield className="w-4 h-4" />, status: 'Pending' },
  ];

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#0a0a0c] border border-arkhe-cyan/30 rounded-xl w-full max-w-4xl h-[70vh] flex flex-col shadow-2xl overflow-hidden">
        <div className="p-6 border-b border-arkhe-cyan/20 flex items-center justify-between bg-arkhe-cyan/5">
          <div className="flex items-center space-x-3">
            <Cpu className="w-6 h-6 text-arkhe-cyan" />
            <h2 className="text-xl font-mono font-bold text-white tracking-widest uppercase">Qubit Sovereignty Pipeline</h2>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="flex-1 overflow-hidden flex flex-col md:flex-row">
          {/* Progress Sidebar */}
          <div className="w-full md:w-64 p-6 border-b md:border-b-0 md:border-r border-arkhe-cyan/10 bg-black/20">
            <h3 className="text-[10px] font-mono text-arkhe-muted uppercase tracking-widest mb-6">Execution Flow</h3>
            <div className="space-y-4">
              {steps.map((s) => (
                <div key={s.id} className={`flex items-start gap-3 p-2 rounded transition-colors ${s.id === step ? 'bg-arkhe-cyan/10 border border-arkhe-cyan/30' : ''}`}>
                  <div className={`mt-0.5 ${s.status === 'Complete' ? 'text-arkhe-green' : s.id === step ? 'text-arkhe-cyan animate-pulse' : 'text-arkhe-muted'}`}>
                    {s.icon}
                  </div>
                  <div>
                    <div className={`text-xs font-mono ${s.id === step ? 'text-white font-bold' : 'text-arkhe-muted'}`}>{s.name}</div>
                    <div className="text-[8px] font-mono text-arkhe-muted/60 uppercase">{s.status}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Main Characterization Area */}
          <div className="flex-1 p-6 space-y-8 overflow-y-auto custom-scrollbar">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="p-4 bg-white/5 border border-arkhe-cyan/10 rounded-lg">
                <div className="text-[10px] font-mono text-arkhe-muted uppercase mb-4">Stability Monitor (DQD Search)</div>
                <div className="h-32 flex items-end justify-between gap-1">
                  {[...Array(20)].map((_, i) => (
                    <div
                      key={i}
                      className="flex-1 bg-arkhe-cyan/40 rounded-t"
                      style={{ height: `${20 + Math.random() * 80}%` }}
                    />
                  ))}
                </div>
                <div className="mt-2 text-center text-[9px] font-mono text-arkhe-cyan">Atrator de Fase [P1, P2]</div>
              </div>

              <div className="p-4 bg-white/5 border border-arkhe-cyan/10 rounded-lg space-y-4">
                <div className="text-[10px] font-mono text-arkhe-muted uppercase">Coherence Metrics</div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-[8px] text-arkhe-muted uppercase">T2* (Dephasing)</div>
                    <div className="text-lg font-mono text-white">{metrics.t2_star} μs</div>
                  </div>
                  <div>
                    <div className="text-[8px] text-arkhe-muted uppercase">T2 (Hahn Echo)</div>
                    <div className="text-lg font-mono text-white">{metrics.t2} μs</div>
                  </div>
                  <div>
                    <div className="text-[8px] text-arkhe-muted uppercase">Gate Fidelity</div>
                    <div className="text-lg font-mono text-arkhe-green">{(metrics.gate_fidelity * 100).toFixed(2)}%</div>
                  </div>
                  <div>
                    <div className="text-[8px] text-arkhe-muted uppercase">SNR (Charge Sensor)</div>
                    <div className="text-lg font-mono text-arkhe-cyan">{metrics.snr.toFixed(1)} dB</div>
                  </div>
                </div>
              </div>
            </div>

            <div className="p-4 bg-black/40 border border-arkhe-cyan/20 rounded-lg">
              <div className="flex items-center gap-2 mb-4">
                <BarChart3 className="w-4 h-4 text-arkhe-cyan" />
                <span className="text-xs font-mono text-white uppercase tracking-widest">Sinfonia do Qubit - Realtime Spectral</span>
              </div>
              <div className="h-40 bg-black/60 rounded flex items-center justify-center border border-white/5">
                <div className="flex items-center gap-1">
                  {[...Array(40)].map((_, i) => (
                    <motion.div
                      key={i}
                      className="w-1 bg-arkhe-cyan"
                      animate={{
                        height: [10, 30, 20, 50, 10, 40, 20],
                        opacity: [0.3, 1, 0.5, 1, 0.3]
                      }}
                      transition={{
                        duration: 2,
                        repeat: Infinity,
                        delay: i * 0.05,
                        ease: "easeInOut"
                      }}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="p-4 bg-black/60 border-t border-arkhe-cyan/20 flex items-center justify-between text-[10px] font-mono">
          <div className="flex items-center gap-4">
            <span className="text-arkhe-muted uppercase">Sovereignty Status:</span>
            <span className="text-arkhe-green font-bold animate-pulse">INCUBATING</span>
          </div>
          <div className="text-arkhe-muted uppercase tracking-widest">Arkhe Block 850.041 // Qubit Pipeline</div>
        </div>
      </div>
    </div>
  );
}
