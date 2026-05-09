/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { motion } from 'framer-motion';
import { X, Activity, Radio, Lock, RefreshCw } from 'lucide-react';
import { useState, useEffect } from 'react';

interface OrbVMLiveMonitorProps {
  onClose: () => void;
}

export default function OrbVMLiveMonitor({ onClose }: OrbVMLiveMonitorProps) {
  const [data, setData] = useState([
    { lambda: 0.9673, lambda2: 0.9358, phi: 5.9810 },
    { lambda: 0.9702, lambda2: 0.9413, phi: 5.9351 },
    { lambda: 0.9769, lambda2: 0.9543, phi: 5.9277 },
    { lambda: 0.9675, lambda2: 0.9361, phi: 5.9481 },
    { lambda: 0.9689, lambda2: 0.9388, phi: 5.9339 },
  ]);

  useEffect(() => {
    const interval = setInterval(() => {
      setData(prev => prev.map(d => ({
        ...d,
        lambda: +(d.lambda + (Math.random() * 0.002 - 0.001)).toFixed(4),
        lambda2: +(d.lambda2 + (Math.random() * 0.002 - 0.001)).toFixed(4),
        phi: +(d.phi + (Math.random() * 0.01 - 0.005)).toFixed(4),
      })));
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.98 }}
        className="bg-[#0a0a0c] border border-arkhe-cyan/30 rounded-xl w-full max-w-4xl overflow-hidden shadow-[0_0_40px_rgba(0,255,170,0.1)] flex flex-col"
      >
        {/* Header */}
        <div className="p-4 border-b border-arkhe-border flex justify-between items-center bg-arkhe-cyan/5">
          <div className="flex items-center gap-3">
            <Radio className="w-5 h-5 text-arkhe-cyan animate-pulse" />
            <div>
              <h2 className="font-mono text-sm uppercase tracking-widest text-white font-bold">
                OrbVM Live Monitor <span className="text-arkhe-muted font-normal">// Phase 3-B</span>
              </h2>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="w-1.5 h-1.5 rounded-full bg-arkhe-green animate-pulse"></span>
                <span className="text-[9px] font-mono text-arkhe-muted uppercase">qHTTP Node Mesh Active</span>
              </div>
            </div>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex flex-1 overflow-hidden h-[400px]">
          {/* Main Monitor Display */}
          <div className="flex-1 p-6 space-y-6 overflow-y-auto custom-scrollbar">
            <div className="grid grid-cols-1 gap-3">
              {data.map((d, i) => (
                <motion.div
                  key={i}
                  initial={{ x: -10, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ delay: i * 0.1 }}
                  className="bg-white/5 border border-white/10 rounded-lg p-4 flex items-center justify-between hover:bg-white/10 transition-colors group"
                >
                  <div className="flex items-center gap-4">
                    <div className="flex flex-col">
                      <span className="text-[9px] font-mono text-arkhe-muted uppercase">Node-0{i+1}</span>
                      <div className="flex items-center gap-2">
                         <div className="w-2 h-2 rounded-full bg-arkhe-cyan"></div>
                         <span className="text-xs font-mono text-white font-bold">STABLE</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex gap-8">
                    <div className="flex flex-col items-center">
                      <span className="text-[8px] font-mono text-arkhe-muted uppercase">λ (Coherence)</span>
                      <span className="text-xs font-mono text-arkhe-cyan">{d.lambda.toFixed(4)}</span>
                    </div>
                    <div className="flex flex-col items-center">
                      <span className="text-[8px] font-mono text-arkhe-muted uppercase">λ₂</span>
                      <span className="text-xs font-mono text-arkhe-cyan">{d.lambda2.toFixed(4)}</span>
                    </div>
                    <div className="flex flex-col items-center">
                      <span className="text-[8px] font-mono text-arkhe-muted uppercase">φ (Phase)</span>
                      <span className="text-xs font-mono text-white">{d.phi.toFixed(4)} rad</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <div className="h-8 w-[1px] bg-white/10 mx-2"></div>
                    <Activity className="w-4 h-4 text-arkhe-green" />
                  </div>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Side Telemetry Panel */}
          <div className="w-72 border-l border-arkhe-border bg-[#0d0e12] p-6 space-y-6">
            <section className="space-y-4">
              <h3 className="text-[10px] font-mono text-arkhe-muted uppercase tracking-widest border-b border-arkhe-border pb-2">Global Consensus</h3>
              <div className="space-y-4">
                <div className="flex justify-between items-end">
                   <div className="flex flex-col">
                      <span className="text-[8px] font-mono text-arkhe-muted uppercase">Kuramoto K</span>
                      <span className="text-sm font-mono text-white font-bold">0.8500</span>
                   </div>
                   <div className="w-24 h-1 bg-white/5 rounded-full overflow-hidden">
                      <div className="h-full bg-arkhe-cyan w-[85%]"></div>
                   </div>
                </div>
                <div className="p-3 bg-arkhe-cyan/10 border border-arkhe-cyan/20 rounded-lg">
                   <div className="flex items-center gap-2 mb-1">
                      <Lock className="w-3 h-3 text-arkhe-cyan" />
                      <span className="text-[9px] font-mono text-arkhe-cyan uppercase font-bold">Spectral Hash Locked</span>
                   </div>
                   <div className="text-[8px] font-mono text-arkhe-muted break-all">
                      1639350205322d0b81405f9673b98369
                   </div>
                </div>
              </div>
            </section>

            <section className="space-y-4">
              <h3 className="text-[10px] font-mono text-arkhe-muted uppercase tracking-widest border-b border-arkhe-border pb-2">Network Proofs</h3>
              <div className="space-y-2">
                 <div className="flex items-center justify-between text-[9px] font-mono">
                    <span className="text-arkhe-muted">ZK_PROOF:</span>
                    <span className="text-arkhe-green">VALIDATED</span>
                 </div>
                 <div className="flex items-center justify-between text-[9px] font-mono">
                    <span className="text-arkhe-muted">RECHARGE:</span>
                    <span className="text-white">2.5M m³</span>
                 </div>
                 <div className="flex items-center justify-between text-[9px] font-mono">
                    <span className="text-arkhe-muted">HYDRO_BAL:</span>
                    <span className="text-arkhe-cyan">0.9768</span>
                 </div>
              </div>
            </section>

            <div className="pt-4 border-t border-arkhe-border">
               <button className="w-full py-2 bg-white/5 border border-white/10 rounded font-mono text-[9px] text-white uppercase tracking-widest hover:bg-white/10 transition-colors flex items-center justify-center gap-2">
                  <RefreshCw className="w-3 h-3" />
                  Full Resync
               </button>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
